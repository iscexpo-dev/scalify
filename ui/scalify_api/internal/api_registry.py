from typing import NamedTuple
from scalify_api.internal.singleton import ProxiedSingleton
from packaging import version as packaging_version


class ScalifyAPIBase(ProxiedSingleton):
    def __init__(self):
        pass


class ScalifyAPIWithVersion(NamedTuple):
    version: str
    api_class: type[ScalifyAPIBase]


def parse_version(version_str: str) -> packaging_version.Version:
    """
    Parses a version string into a packaging_version.Version object.
    Raises ValueError if the version string is invalid.
    """
    if version_str == "latest":
        return packaging_version.parse("9999999.9999999.9999999")
    return packaging_version.parse(version_str)


registered_versions: list[ScalifyAPIWithVersion] = []


def register_versions(versions: list[ScalifyAPIWithVersion]):
    versions.sort(key=lambda x: parse_version(x.version))
    global registered_versions
    registered_versions = versions


def get_all_versions() -> list[ScalifyAPIWithVersion]:
    """
    Returns a list of all registered ScalifyAPI versions.
    """
    return registered_versions
