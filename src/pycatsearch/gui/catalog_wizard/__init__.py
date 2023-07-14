# -*- coding: utf-8 -*-
from __future__ import annotations

import abc
from pathlib import Path

from qtpy.QtWidgets import QDialog, QMessageBox, QWidget, QWizard
from qtpy.compat import getsavefilename

from ..save_catalog_waiting_screen import SaveCatalogWaitingScreen
from ...catalog import CatalogType

__all__ = ['SaveCatalogWizard']


class SaveCatalogWizard(QWizard):
    def __init__(self,
                 default_save_location: Path | None = None,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.catalog: CatalogType = dict()
        self.default_save_location: Path | None = default_save_location

        self.setModal(True)
        if parent is not None:
            self.setWindowIcon(parent.windowIcon())

    def _get_save_file_name(self, directory: str = '') -> tuple[str, str]:

        formats: dict[tuple[str, ...], str] = {
            ('.json.gz',): self.tr('JSON with GZip compression', 'file type'),
            ('.json.bz2',): self.tr('JSON with Bzip2 compression', 'file type'),
            ('.json.xz', '.json.lzma',): self.tr('JSON with LZMA2 compression', 'file type'),
            ('.json',): self.tr('JSON', 'file type'),
        }

        def join_file_dialog_formats(_formats: dict[tuple[str, ...], str]) -> str:
            f: tuple[str, ...]
            all_supported_extensions: list[str] = []
            for f in _formats.keys():
                all_supported_extensions.extend(ensure_prefix(_f, '*') for _f in f)
            format_lines: list[str] = [''.join((
                self.tr('All supported', 'file type'),
                '(',
                ' '.join(ensure_prefix(_f, '*') for _f in all_supported_extensions),
                ')'))]
            n: str
            for f, n in _formats.items():
                format_lines.append(''.join((n, '(', ' '.join(ensure_prefix(_f, '*') for _f in f), ')')))
            format_lines.append(self.tr('All files', 'file type') + '(* *.*)')
            return ';;'.join(format_lines)

        filename: str
        _filter: str
        filename, _filter = getsavefilename(self,
                                            caption=self.tr('Save As…'),
                                            filters=join_file_dialog_formats(formats),
                                            basedir=directory)
        return filename, _filter

    @abc.abstractmethod
    def frequency_limits(self) -> tuple[float, float]:
        ...

    def done(self, exit_code: QDialog.DialogCode) -> None:
        ws: SaveCatalogWaitingScreen
        if exit_code == QDialog.DialogCode.Accepted and self.catalog:
            if self.default_save_location is not None:
                try:
                    ws = SaveCatalogWaitingScreen(
                        self,
                        filename=self.default_save_location,
                        catalog=self.catalog,
                        frequency_limits=self.frequency_limits()
                    )
                    ws.exec()
                except OSError as ex:
                    QMessageBox.warning(
                        self,
                        self.tr('Unable to save the catalog'),
                        self.tr('Error {exception} occurred while saving {filename}. Try another location.')
                        .format(exception=ex, filename=self.default_save_location)
                    )
                else:
                    return super(SaveCatalogWizard, self).done(exit_code)

            save_file_name: str
            while True:
                save_file_name, _ = self._get_save_file_name()
                if not save_file_name:
                    return super(SaveCatalogWizard, self).done(QDialog.DialogCode.Rejected)

                try:
                    ws = SaveCatalogWaitingScreen(
                        self,
                        filename=save_file_name,
                        catalog=self.catalog,
                        frequency_limits=self.frequency_limits()
                    )
                    ws.exec()
                except OSError as ex:
                    QMessageBox.warning(
                        self,
                        self.tr('Unable to save the catalog'),
                        self.tr('Error {exception} occurred while saving {filename}. Try another location.')
                        .format(exception=ex, filename=save_file_name)
                    )
                else:
                    return super(SaveCatalogWizard, self).done(exit_code)

        return super(SaveCatalogWizard, self).done(exit_code)
