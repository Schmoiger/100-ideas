"""Book Mode and Typst Typesetting Subsystem package."""

from services.typesetting.compiler import (
    compile_aggregated_book,
    compile_all_volumes,
    compile_chapter_pdf,
    compile_volume_pdf,
)
from services.typesetting.pipeline import (
    process_aggregated_book,
    process_all_volumes,
    process_book_chapter,
    process_volume_book,
)
from services.typesetting.volumes import (
    VolumeChapterRef,
    VolumeConfig,
    VolumePart,
    get_default_volumes_path,
    load_volumes_config,
)

__version__ = "0.1.0"

__all__ = [
    "VolumeChapterRef",
    "VolumeConfig",
    "VolumePart",
    "compile_aggregated_book",
    "compile_all_volumes",
    "compile_chapter_pdf",
    "compile_volume_pdf",
    "get_default_volumes_path",
    "load_volumes_config",
    "process_all_volumes",
    "process_aggregated_book",
    "process_book_chapter",
    "process_volume_book",
]
