# -*- coding: utf-8 -*-
from __future__ import annotations

from qtpy import PYSIDE6
from qtpy.QtWidgets import QWidget
from qtpy.compat import getopenfilenames, getsavefilename

from ..utils import ensure_prefix

__all__ = ["FileDialogSource"]


class FileDialogSource(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        if not PYSIDE6:
            super().__init__(parent)

    def _join_file_dialog_formats(self, formats: dict[tuple[str, ...], str]) -> str:
        f: tuple[str, ...]
        all_supported_extensions: list[str] = []
        for f in formats.keys():
            all_supported_extensions.extend(ensure_prefix(_f, "*") for _f in f)
        format_lines: list[str] = [
            "".join(
                (
                    self.tr("All supported", "file type"),
                    "(",
                    " ".join(ensure_prefix(_f, "*") for _f in all_supported_extensions),
                    ")",
                )
            )
        ]
        n: str
        for f, n in formats.items():
            format_lines.append("".join((n, "(", " ".join(ensure_prefix(_f, "*") for _f in f), ")")))
        format_lines.append(self.tr("All files", "file type") + "(* *.*)")
        return ";;".join(format_lines)

    def get_open_file_names(self, directory: str = "") -> tuple[list[str], str]:
        formats: dict[tuple[str, ...], str] = {
            (".json.gz", ".json.bz2", ".json.xz", ".json.lzma"): self.tr("Compressed JSON", "file type"),
            (".json",): self.tr("JSON", "file type"),
        }

        filename: list[str]
        _filter: str
        filename, _filter = getopenfilenames(
            self,
            caption=self.tr("Load Catalog"),
            filters=self._join_file_dialog_formats(formats),
            basedir=directory,
        )
        return filename, _filter

    def get_save_file_name(self, directory: str = "") -> tuple[str, str]:
        formats: dict[tuple[str, ...], str] = {
            (".json.gz",): self.tr("JSON with GZip compression", "file type"),
            (".json.bz2",): self.tr("JSON with Bzip2 compression", "file type"),
            (
                ".json.xz",
                ".json.lzma",
            ): self.tr("JSON with LZMA2 compression", "file type"),
            (".json",): self.tr("JSON", "file type"),
        }

        filename: str
        _filter: str
        filename, _filter = getsavefilename(
            self,
            caption=self.tr("Save As…"),
            filters=self._join_file_dialog_formats(formats),
            basedir=directory,
        )
        return filename, _filter
