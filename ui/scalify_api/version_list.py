from scalify_api.latest import ScalifyAPI_latest
from scalify_api.v0_0_2 import ScalifyAPIAdapter_v0_0_2
from scalify_api.v0_0_1 import ScalifyAPIAdapter_v0_0_1
from scalify_api.internal import ScalifyAPIBase

supported_versions: list[type[ScalifyAPIBase]] = [
    ScalifyAPI_latest,
    ScalifyAPIAdapter_v0_0_2,
    ScalifyAPIAdapter_v0_0_1,
]

