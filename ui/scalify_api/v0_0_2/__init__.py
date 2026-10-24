from scalify_api.latest import (
    ScalifyAPI_latest,
    Input as Input_latest,
    InputImpl as InputImpl_latest,
    Types as Types_latest,
)
from typing import Type, TYPE_CHECKING
from scalify_api.internal.async_to_sync import create_sync_class
from scalify_api.latest import io, ui, IO, UI, ScalifyExtension  #noqa: F401


class ScalifyAPIAdapter_v0_0_2(ScalifyAPI_latest):
    VERSION = "0.0.2"
    STABLE = False


class Input(Input_latest):
    pass


class InputImpl(InputImpl_latest):
    pass


class Types(Types_latest):
    pass


ScalifyAPI = ScalifyAPIAdapter_v0_0_2

# Create a synchronous version of the API
if TYPE_CHECKING:
    from scalify_api.v0_0_2.generated.ScalifyAPISyncStub import ScalifyAPISyncStub  # type: ignore

    ScalifyAPISync: Type[ScalifyAPISyncStub]
ScalifyAPISync = create_sync_class(ScalifyAPIAdapter_v0_0_2)

__all__ = [
    "ScalifyAPI",
    "ScalifyAPISync",
    "Input",
    "InputImpl",
    "Types",
    "ScalifyExtension",
    "io",
    "IO",
    "ui",
    "UI",
]
