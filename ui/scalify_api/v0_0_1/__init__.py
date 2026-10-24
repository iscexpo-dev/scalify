from scalify_api.v0_0_2 import (
    ScalifyAPIAdapter_v0_0_2,
    Input as Input_v0_0_2,
    InputImpl as InputImpl_v0_0_2,
    Types as Types_v0_0_2,
)
from typing import Type, TYPE_CHECKING
from scalify_api.internal.async_to_sync import create_sync_class


# This version only exists to serve as a template for future version adapters.
# There is no reason anyone should ever use it.
class ScalifyAPIAdapter_v0_0_1(ScalifyAPIAdapter_v0_0_2):
    VERSION = "0.0.1"
    STABLE = True

class Input(Input_v0_0_2):
    pass

class InputImpl(InputImpl_v0_0_2):
    pass

class Types(Types_v0_0_2):
    pass

ScalifyAPI = ScalifyAPIAdapter_v0_0_1

# Create a synchronous version of the API
if TYPE_CHECKING:
    from scalify_api.v0_0_1.generated.ScalifyAPISyncStub import ScalifyAPISyncStub  # type: ignore

    ScalifyAPISync: Type[ScalifyAPISyncStub]

ScalifyAPISync = create_sync_class(ScalifyAPIAdapter_v0_0_1)

__all__ = [
    "ScalifyAPI",
    "ScalifyAPISync",
    "Input",
    "InputImpl",
    "Types",
]
