# -*- coding: utf-8 -*-
from __future__ import annotations

import abc
from pathlib import Path

from qtpy.QtWidgets import QDialog, QMessageBox, QWidget, QWizard

from ..catalog_file_dialog import CatalogSaveFileDialog
from ..save_catalog_waiting_screen import SaveCatalogWaitingScreen
from ..settings import Settings
from ...catalog import CatalogType

__all__ = ["SaveCatalogWizard"]


class SaveCatalogWizard(QWizard):
    def __init__(
        self,
        settings: Settings,
        default_save_location: Path | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.catalog: CatalogType = dict()
        self.default_save_location: Path | None = default_save_location

        self.save_dialog: CatalogSaveFileDialog = CatalogSaveFileDialog(settings=settings, parent=self)

        self.setModal(True)
        if parent is not None:
            self.setWindowIcon(parent.windowIcon())

    @abc.abstractmethod
    def frequency_limits(self) -> tuple[float, float]: ...

    def done(self, exit_code: QDialog.DialogCode) -> None:
        ws: SaveCatalogWaitingScreen
        if exit_code == QDialog.DialogCode.Accepted and self.catalog:
            if self.default_save_location is not None:
                try:
                    ws = SaveCatalogWaitingScreen(
                        self,
                        filename=self.default_save_location,
                        catalog=self.catalog,
                        frequency_limits=self.frequency_limits(),
                    )
                    ws.exec()
                except OSError as ex:
                    QMessageBox.warning(
                        self,
                        self.tr("Unable to save the catalog"),
                        self.tr("Error {exception} occurred while saving {filename}. Try another location.").format(
                            exception=ex,
                            filename=self.default_save_location,
                        ),
                    )
                else:
                    return super(SaveCatalogWizard, self).done(exit_code)

            save_filename: Path | None
            while True:
                if not (save_filename := self.save_dialog.get_save_filename()):
                    return super(SaveCatalogWizard, self).done(QDialog.DialogCode.Rejected)

                try:
                    ws = SaveCatalogWaitingScreen(
                        self,
                        filename=save_filename,
                        catalog=self.catalog,
                        frequency_limits=self.frequency_limits(),
                    )
                    ws.exec()
                except OSError as ex:
                    QMessageBox.warning(
                        self,
                        self.tr("Unable to save the catalog"),
                        self.tr(
                            "Error {exception} occurred while saving {filename}. Try another location.",
                        ).format(exception=ex, filename=save_filename),
                    )
                else:
                    return super(SaveCatalogWizard, self).done(exit_code)

        return super(SaveCatalogWizard, self).done(exit_code)
