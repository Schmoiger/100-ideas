"""Book Mode and Typst Typesetting Subsystem package."""

from services.typesetting.volumes import (
    VolumeChapterRef,
    VolumeConfig,
    VolumePart,
    load_volumes_config,
)

__version__ = "0.1.0"

__all__ = [
    "VolumeChapterRef",
    "VolumeConfig",
    "VolumePart",
    "load_volumes_config",
]
