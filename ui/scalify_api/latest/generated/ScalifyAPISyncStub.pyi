from typing import Any, Dict, List, Optional, Tuple, Union, Set, Sequence, cast, NamedTuple
from scalify_api.latest import ScalifyAPI_latest
from PIL.Image import Image
from torch import Tensor
class ScalifyAPISyncStub:
    def __init__(self) -> None: ...

    class ExecutionSync:
        def __init__(self) -> None: ...
        """
        Update the progress bar displayed in the ScalifyUI interface.

        This function allows custom nodes and API calls to report their progress
        back to the user interface, providing visual feedback during long operations.

        Migration from previous API: scalify.utils.PROGRESS_BAR_HOOK
        """
        def set_progress(self, value: float, max_value: float, node_id: Union[str, None] = None, preview_image: Union[Image, Tensor, None] = None, ignore_size_limit: bool = False) -> None: ...

    execution: ExecutionSync
