# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import final

from qtpy.QtCore import QCoreApplication
from qtpy.QtWidgets import QWidget

from .file_dialog import OpenFileDialog, SaveFileDialog
from .settings import Settings

__all__ = ["CatalogOpenFileDialog", "CatalogSaveFileDialog"]

_translate = QCoreApplication.translate

supported_name_filters = [
    OpenFileDialog.SupportedNameFilterItem(
        required_packages=["gzip"],
        name=_translate("file type", "JSON with GZip compression"),
        file_extensions=[".json.gz"],
    ),
    OpenFileDialog.SupportedNameFilterItem(
        required_packages=["bz2"],
        name=_translate("file type", "JSON with Bzip2 compression"),
        file_extensions=[".json.bz2"],
    ),
    OpenFileDialog.SupportedNameFilterItem(
        required_packages=["lzma"],
        name=_translate("file type", "JSON with LZMA2 compression"),
        file_extensions=[".json.xz", ".json.lzma"],
    ),
]

supported_mimetype_filters = [
    OpenFileDialog.SupportedMimetypeItem(
        required_packages=[],
        file_extension=".json",
    ),
]


@final
class CatalogOpenFileDialog(OpenFileDialog):
    def __init__(
        self,
        settings: Settings,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(
            settings=settings,
            supported_name_filters=supported_name_filters,
            supported_mimetype_filters=supported_mimetype_filters,
            parent=parent,
        )


@final
class CatalogSaveFileDialog(SaveFileDialog):
    def __init__(
        self,
        settings: Settings,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(
            settings=settings,
            supported_name_filters=supported_name_filters,
            supported_mimetype_filters=supported_mimetype_filters,
            parent=parent,
        )
