from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
from scalify_api.internal import ScalifyAPIBase
from scalify_api.internal.singleton import ProxiedSingleton
from scalify_api.internal.async_to_sync import create_sync_class
from ._input import ImageInput, AudioInput, MaskInput, LatentInput, VideoInput
from ._input_impl import VideoFromFile, VideoFromComponents, VideoFromList
from ._util import VideoCodec, VideoContainer, VideoComponents, MESH, VOXEL, SPLAT, File3D
from . import _io_public as io
from . import _ui_public as ui
from scalify_execution.utils import get_executing_context
from scalify_execution.progress import get_progress_state, PreviewImageTuple
from PIL import Image
from scalify.cli_args import args
import numpy as np


class ScalifyAPI_latest(ScalifyAPIBase):
    VERSION = "latest"
    STABLE = False

    def __init__(self):
        super().__init__()
        self.node_replacement = self.NodeReplacement()
        self.execution = self.Execution()
        self.caching = self.Caching()

    class NodeReplacement(ProxiedSingleton):
        async def register(self, node_replace: io.NodeReplace) -> None:
            """Register a node replacement mapping."""
            from server import PromptServer
            PromptServer.instance.node_replace_manager.register(node_replace)

    class Execution(ProxiedSingleton):
        async def set_progress(
            self,
            value: float,
            max_value: float,
            node_id: str | None = None,
            preview_image: Image.Image | ImageInput | None = None,
            ignore_size_limit: bool = False,
        ) -> None:
            """
            Update the progress bar displayed in the ScalifyUI interface.

            This function allows custom nodes and API calls to report their progress
            back to the user interface, providing visual feedback during long operations.

            Migration from previous API: scalify.utils.PROGRESS_BAR_HOOK
            """
            executing_context = get_executing_context()
            if node_id is None and executing_context is not None:
                node_id = executing_context.node_id
            if node_id is None:
                raise ValueError("node_id must be provided if not in executing context")

            # Convert preview_image to PreviewImageTuple if needed
            to_display: PreviewImageTuple | Image.Image | ImageInput | None = preview_image
            if to_display is not None:
                # First convert to PIL Image if needed
                if isinstance(to_display, ImageInput):
                    # Convert ImageInput (torch.Tensor) to PIL Image
                    # Handle tensor shape [B, H, W, C] -> get first image if batch
                    tensor = to_display
                    if len(tensor.shape) == 4:
                        tensor = tensor[0]

                    # Convert to numpy array and scale to 0-255
                    image_np = (tensor.cpu().numpy() * 255).astype(np.uint8)
                    to_display = Image.fromarray(image_np)

                if isinstance(to_display, Image.Image):
                    # Detect image format from PIL Image
                    image_format = to_display.format if to_display.format else "JPEG"
                    # Use None for preview_size if ignore_size_limit is True
                    preview_size = None if ignore_size_limit else args.preview_size
                    to_display = (image_format, to_display, preview_size)

            get_progress_state().update_progress(
                node_id=node_id,
                value=value,
                max_value=max_value,
                image=to_display,
            )

    class Caching(ProxiedSingleton):
        """
        External cache provider API for sharing cached node outputs
        across ScalifyUI instances.

        Example::

            from scalify_api.latest import Caching

            class MyCacheProvider(Caching.CacheProvider):
                async def on_lookup(self, context):
                    ...  # check external storage

                async def on_store(self, context, value):
                    ...  # store to external storage

            Caching.register_provider(MyCacheProvider())
        """
        from ._caching import CacheProvider, CacheContext, CacheValue

        async def register_provider(self, provider: "ScalifyAPI_latest.Caching.CacheProvider") -> None:
            """Register an external cache provider. Providers are called in registration order."""
            from scalify_execution.cache_provider import register_cache_provider
            register_cache_provider(provider)

        async def unregister_provider(self, provider: "ScalifyAPI_latest.Caching.CacheProvider") -> None:
            """Unregister a previously registered cache provider."""
            from scalify_execution.cache_provider import unregister_cache_provider
            unregister_cache_provider(provider)

class ScalifyExtension(ABC):
    async def on_load(self) -> None:
        """
        Called when an extension is loaded.
        This should be used to initialize any global resources needed by the extension.
        """

    @abstractmethod
    async def get_node_list(self) -> list[type[io.ScalifyNode]]:
        """
        Returns a list of nodes that this extension provides.
        """

class Input:
    Image = ImageInput
    Audio = AudioInput
    Mask = MaskInput
    Latent = LatentInput
    Video = VideoInput

class InputImpl:
    VideoFromFile = VideoFromFile
    VideoFromComponents = VideoFromComponents
    VideoFromList = VideoFromList

class Types:
    VideoCodec = VideoCodec
    VideoContainer = VideoContainer
    VideoComponents = VideoComponents
    MESH = MESH
    VOXEL = VOXEL
    SPLAT = SPLAT
    File3D = File3D


Caching = ScalifyAPI_latest.Caching

ScalifyAPI = ScalifyAPI_latest

# Create a synchronous version of the API
if TYPE_CHECKING:
    import scalify_api.latest.generated.ScalifyAPISyncStub  # type: ignore

    ScalifyAPISync: type[scalify_api.latest.generated.ScalifyAPISyncStub.ScalifyAPISyncStub]
ScalifyAPISync = create_sync_class(ScalifyAPI_latest)

# create new aliases for io and ui
IO = io
UI = ui

__all__ = [
    "ScalifyAPI",
    "ScalifyAPISync",
    "Input",
    "InputImpl",
    "Types",
    "Caching",
    "ScalifyExtension",
    "io",
    "IO",
    "ui",
    "UI",
]
