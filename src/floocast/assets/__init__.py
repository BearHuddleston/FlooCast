"""Asset loading utilities."""

import sys
from importlib import resources
from pathlib import Path


def get_asset_path(name: str) -> Path:
    """Get the path to an asset file.

    Works both in development (source) and when installed as a package.
    """
    if sys.version_info >= (3, 11):
        return resources.files(__package__).joinpath(name)
    else:
        with resources.as_file(resources.files(__package__).joinpath(name)) as path:
            return path


def get_asset_dir() -> Path:
    """Get the path to the assets directory."""
    if sys.version_info >= (3, 11):
        return resources.files(__package__)
    else:
        with resources.as_file(resources.files(__package__)) as path:
            return path
