from typing_extensions import override
from scalify_api.latest import ScalifyExtension, io
from scalify_api.torch_helpers import set_torch_compile_wrapper

def skip_torch_compile_dict(guard_entries):
    return [("transformer_options" not in entry.name) for entry in guard_entries]

class TorchCompileModel(io.ScalifyNode):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="TorchCompileModel",
            category="experimental",
            inputs=[
                io.Model.Input("model"),
                io.Combo.Input(
                    "backend",
                    options=["inductor", "cudagraphs"],
                    advanced=True,
                ),
            ],
            outputs=[io.Model.Output()],
            is_experimental=True,
        )

    @classmethod
    def execute(cls, model, backend) -> io.NodeOutput:
        m = model.clone(disable_dynamic=True)
        set_torch_compile_wrapper(model=m, backend=backend, options={"guard_filter_fn": skip_torch_compile_dict})
        return io.NodeOutput(m)


class TorchCompileExtension(ScalifyExtension):
    @override
    async def get_node_list(self) -> list[type[io.ScalifyNode]]:
        return [
            TorchCompileModel,
        ]


async def scalify_entrypoint() -> TorchCompileExtension:
    return TorchCompileExtension()
