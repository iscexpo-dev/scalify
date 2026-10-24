import logging
import threading
import warnings
import weakref

import scalify_kitchen as ck
import torch

import scalify_aimdo.malloc_graph
import scalify_aimdo.model_vbar
from scalify.cli_args import args
import scalify.memory_management
import scalify.model_management
import scalify.ops

PREFETCH_QUEUES = []
GRAPH_WARMED_MODULES = weakref.WeakSet()
GRAPH_CAPTURE_STREAMS = {}
MALLOC_GRAPHS = {}
MALLOC_GRAPH_BREAKS = 0
MALLOC_GRAPH_ROGUES = 0
MALLOC_GRAPH_USED = False

def _malloc_graph_break():
    global MALLOC_GRAPH_BREAKS
    MALLOC_GRAPH_BREAKS += 1
    logging.debug("Scalify model compiler graph break")

def malloc_graph_enabled(device):
    return not args.disable_scalify_compiler and scalify.memory_management.aimdo_enabled and scalify.model_management.is_device_cuda(device)

class _PauseMallocGraph:
    def __init__(self, sync=False):
        self.sync = sync

    def __enter__(self):
        graph = MALLOC_GRAPHS.get(threading.get_ident())
        if graph is not None and graph._scalify_active:
            graph.pause(sync=self.sync)

    def __exit__(self, *args):
        graph = MALLOC_GRAPHS.get(threading.get_ident())
        if graph is not None and graph._scalify_active:
            graph.resume(sync=self.sync)

def pause_malloc_graph(sync=False):
    return _PauseMallocGraph(sync)

class _MallocGraphScope:
    def __init__(self, device):
        self.device = device

    def __enter__(self):
        malloc_graph_begin(self.device)

    def __exit__(self, exc_type, *args):
        if exc_type is None:
            malloc_graph_end()
        else:
            cleanup_malloc_graph()

def malloc_graph_scope(device):
    return _MallocGraphScope(device)

def malloc_graph_begin(device):
    global MALLOC_GRAPH_USED
    if not malloc_graph_enabled(device):
        return
    thread_id = threading.get_ident()
    graph = MALLOC_GRAPHS.get(thread_id)
    if graph is None:
        graph = scalify_aimdo.malloc_graph.record(
            scalify.model_management.current_stream(device), args.assert_graph_breaks
        )
        graph._scalify_cuda_graph_modules = weakref.WeakSet()
        MALLOC_GRAPHS[thread_id] = graph
    else:
        graph.push()
    if hasattr(ck, "set_allocation_context"):
        ck.set_allocation_context(pause_malloc_graph())
    graph._scalify_active = True
    MALLOC_GRAPH_USED = True

def malloc_graph_end():
    thread_id = threading.get_ident()
    graph = MALLOC_GRAPHS.get(thread_id)
    if graph is not None and graph._scalify_active:
        if graph.pop():
            _malloc_graph_break()
        graph._scalify_active = False

def cleanup_malloc_graph():
    global MALLOC_GRAPH_ROGUES

    graph = MALLOC_GRAPHS.pop(threading.get_ident(), None)
    if graph is not None:
        if graph._scalify_active:
            graph.abort()
            graph._scalify_active = False
        else:
            scalify.model_management.synchronize()
        for module in graph._scalify_cuda_graph_modules:
            _drop_graph(module)
        MALLOC_GRAPH_ROGUES += graph.rogue_count
        del graph

def pin_modules(scalify_modules, device, dtype=None):
    registerable_size = 0
    for s in scalify_modules:
        registerable_size += scalify.memory_management.vram_aligned_size([s.weight, s.bias])
        for param_key in ("weight", "bias"):
            lowvram_fn = getattr(s, param_key + "_lowvram_function", None)
            if lowvram_fn is not None:
                registerable_size += lowvram_fn.memory_required()

    offload_stream, fully_faulted = scalify.ops.cast_modules_with_vbar(scalify_modules, None, device, None, True, return_faulted=True)
    if not (scalify_modules and scalify_modules[0]._pin_state["fast_disk"]):
        scalify.model_management.ensure_pin_registerable(registerable_size)
    scalify.model_management.sync_stream(device, offload_stream)
    if fully_faulted and dtype is not None:
        for scalify_module in scalify_modules:
            scalify.ops.resolve_cast_module_with_vbar(scalify_module, dtype, device, dtype, None, False, return_weights=False)
    return offload_stream, fully_faulted

def cleanup_prefetched_modules(module, scalify_modules):
    for s in scalify_modules:
        prefetch = getattr(s, "_prefetch", None)
        if prefetch is None:
            continue
        for param_key in ("weight", "bias"):
            lowvram_fn = getattr(s, param_key + "_lowvram_function", None)
            if lowvram_fn is not None:
                lowvram_fn.clear_prepared()
        if prefetch["signature"] is not None:
            scalify_aimdo.model_vbar.vbar_unpin(s._v)
        delattr(s, "_prefetch")
    if getattr(module, "_v_block_faulted", False):
        scalify_aimdo.model_vbar.vbar_unpin(module._v_block)
        del module._v_block_faulted

def _drop_graph(module):
    graph = getattr(module, "_scalify_graph", None)
    if graph is None:
        return
    # reset() through the bound method surfaces the allocator's benign
    # "uncaptured free of a captured allocation" as catchable Python warnings;
    # a plain del frees from the C++ dealloc path and spams stderr instead
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        graph["graph"].reset()
    del module._scalify_graph

def cleanup_prefetch_queues():
    global PREFETCH_QUEUES
    global MALLOC_GRAPH_BREAKS
    global MALLOC_GRAPH_ROGUES
    global MALLOC_GRAPH_USED

    cleanup_malloc_graph()
    for queue in PREFETCH_QUEUES:
        # Only the head has been prefetched; later entries are raw module groups.
        if queue[0] is not None:
            _, (prefetched_module, scalify_modules) = queue[0]
            cleanup_prefetched_modules(prefetched_module, scalify_modules)
    PREFETCH_QUEUES = []
    GRAPH_WARMED_MODULES.clear()
    if MALLOC_GRAPH_USED:
        logging.info("Scalify model compiler graph breaks: %d, rogues: %d", MALLOC_GRAPH_BREAKS, MALLOC_GRAPH_ROGUES)
    MALLOC_GRAPH_BREAKS = 0
    MALLOC_GRAPH_ROGUES = 0
    MALLOC_GRAPH_USED = False

def prefetch_queue_pop(queue, device, module, dtype=None, core=None, enable_graph=False, generator=None, malloc_scope=None):
    malloc_graph = MALLOC_GRAPHS.get(threading.get_ident())
    if malloc_graph is not None and not malloc_graph._scalify_active:
        malloc_graph = None
    enable_graph = enable_graph and malloc_graph is not None and not args.disable_cuda_graphs and scalify.model_management.is_device_cuda(device) and getattr(module, "_v_block", None) is not None
    if queue is None:
        if malloc_graph is not None and malloc_scope is not None:
            if malloc_graph.iterate(malloc_scope if module is not None else None):
                _malloc_graph_break()
        if core is not None:
            core()
        return

    capture_stream = None
    if enable_graph:
        capture_stream = GRAPH_CAPTURE_STREAMS.get(device)
        if capture_stream is None:
            capture_stream = torch.cuda.Stream(device=device)
            # Keep PyTorch's persistent BLAS workspaces outside the allocation graph.
            malloc_graph.pause()
            with torch.cuda.stream(capture_stream):
                torch.cuda.current_blas_handle()
                one = torch.empty((2, 2), device=device)
                torch.addmm(one[0], one, one)
            malloc_graph.resume()
            GRAPH_CAPTURE_STREAMS[device] = capture_stream

    signature = None
    graph_hit = False
    graph = getattr(module, "_scalify_graph", None) if enable_graph else None
    if graph is not None:
        signature = scalify_aimdo.model_vbar.vbar_fault(module._v_block)
        if signature is not None:
            module._v_block_faulted = True
            graph_hit = scalify_aimdo.model_vbar.vbar_signature_compare(signature, graph["signature"])

    if malloc_graph is not None and malloc_scope is not None:
        if malloc_graph.iterate(malloc_scope if module is not None and not graph_hit else None):
            _malloc_graph_break()

    consumed = queue.pop(0)
    if consumed is not None:
        offload_stream, prefetch_state = consumed
        if offload_stream is not None:
            offload_stream.wait_stream(scalify.model_management.current_stream(device))
        prefetched_module, scalify_modules = prefetch_state
        if scalify_modules is not None:
            cleanup_prefetched_modules(prefetched_module, scalify_modules)

    if graph_hit:
        queue[0] = (None, (module, []))
        graph["graph"].replay()
        return

    fully_faulted = False
    prefetch = queue[0]
    if prefetch is not None:
        scalify_modules = []
        prefetch_modules = prefetch if isinstance(prefetch, (list, tuple)) else (prefetch,)
        for root in prefetch_modules:
            for s in root.modules():
                if hasattr(s, "_v"):
                    scalify_modules.append(s)

        # Keep partially pinned groups reachable if pinning raises.
        queue[0] = (None, (module, scalify_modules))
        offload_stream, fully_faulted = pin_modules(scalify_modules, device, dtype)
        queue[0] = (offload_stream, (module, scalify_modules))

    if core is not None:
        if enable_graph and fully_faulted and module in GRAPH_WARMED_MODULES:
            if signature is None:
                signature = scalify_aimdo.model_vbar.vbar_fault(module._v_block)
                if signature is not None:
                    module._v_block_faulted = True
            if signature is not None:
                _drop_graph(module)
                malloc_graph.pause()
                graph = torch.cuda.CUDAGraph()
                if generator is not None:
                    graph.register_generator_state(generator)
                malloc_graph.resume()
                # Capture-time VBAR eviction is safe after prior work completes.
                scalify.model_management.synchronize()
                capture_stream.wait_stream(scalify.model_management.current_stream(device))
                malloc_graph.pause(sync=True)
                with malloc_graph.use_stream(capture_stream):
                    with torch.cuda.graph(graph, stream=capture_stream, capture_error_mode="thread_local"):
                        malloc_graph.resume()
                        core()
                        malloc_graph.pause()
                malloc_graph.resume(sync=True)
                scalify.model_management.current_stream(device).wait_stream(capture_stream)
                graph.replay()
                module._scalify_graph = {"graph": graph, "signature": signature}
                malloc_graph._scalify_cuda_graph_modules.add(module)
                return
        if capture_stream is None:
            core()
        else:
            capture_stream.wait_stream(scalify.model_management.current_stream(device))
            with torch.cuda.stream(capture_stream), malloc_graph.use_stream(capture_stream):
                core()
            scalify.model_management.current_stream(device).wait_stream(capture_stream)
            GRAPH_WARMED_MODULES.add(module)

def make_prefetch_queue(queue, device, transformer_options):
    if (not transformer_options.get("prefetch_dynamic_vbars", False)
        or scalify.model_management.NUM_STREAMS == 0
        or scalify.model_management.is_device_cpu(device)
        or not scalify.model_management.device_supports_non_blocking(device)):
        return None

    queue = [None] + queue + [None]
    PREFETCH_QUEUES.append(queue)
    return queue
