# -*- coding: utf-8 -*-
from __future__ import annotations

from math import nan
from os import PathLike
from pathlib import Path

from qtpy.QtWidgets import QDialog, QWidget

from .catalog_wizard import SaveCatalogWizard
from .catalog_wizard.download_confirmation_page import DownloadConfirmationPage
from .catalog_wizard.progress_page import ProgressPage
from .catalog_wizard.settings_page import SettingsPage
from .catalog_wizard.summary_page import SummaryPage
from .settings import Settings
from ..catalog import Catalog

__all__ = ["UpdateDialog"]


class UpdateDialog(SaveCatalogWizard):
    """GUI for `async_downloader.Downloader` or `downloader.Downloader`"""

    def __init__(
        self,
        settings: Settings,
        existing_catalog_location: str | PathLike[str],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(settings=settings, parent=parent, default_save_location=Path(existing_catalog_location))

        self._old_catalog: Catalog = Catalog(existing_catalog_location)

        self.setWindowTitle(self.tr("Update Catalog"))

        self._settings_page: SettingsPage = SettingsPage(self)
        self.addPage(self._settings_page)
        self.addPage(DownloadConfirmationPage(self))
        self._progress_page: ProgressPage = ProgressPage(self, existing_catalog=self._old_catalog)
        self.addPage(self._progress_page)
        self.addPage(SummaryPage(self))

        if self._old_catalog:
            self._settings_page.frequency_limits = self.frequency_limits()
        else:
            self._progress_page.setCommitPage(True)
            self.setStartId(self._progress_page.nextId())

        # don't show `self._settings_page`
        self._settings_page.setCommitPage(True)
        self.setStartId(self._settings_page.nextId())

    def back(self) -> None:
        if self._progress_page.isActive():
            self._progress_page.stop()
        super().back()

    def next(self) -> None:
        if self._progress_page.isActive():
            self._progress_page.stop()
        super().next()

    def restart(self) -> None:
        if self._progress_page.isActive():
            self._progress_page.stop()
        super().restart()

    def frequency_limits(self) -> tuple[float, float]:
        if not self._old_catalog:
            return nan, nan
        return self._old_catalog.min_frequency, self._old_catalog.max_frequency

    def done(self, exit_code: QDialog.DialogCode) -> None:
        if self._progress_page.isActive():
            self._progress_page.stop()
        return super().done(exit_code)
