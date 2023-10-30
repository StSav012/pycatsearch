# -*- coding: utf-8 -*-
from __future__ import annotations

from queue import Queue
from typing import cast

from qtpy.QtCore import QTimer, Slot
from qtpy.QtWidgets import QProgressBar, QVBoxLayout, QWidget, QWizard, QWizardPage

from . import SaveCatalogWizard
from ...catalog import Catalog

try:
    from ...async_downloader import Downloader
except (SyntaxError, ImportError, ModuleNotFoundError):
    from ...downloader import Downloader

__all__ = ["ProgressPage"]


class ProgressPage(QWizardPage):
    def __init__(self, parent: QWidget | None = None, existing_catalog: Catalog | None = None) -> None:
        super().__init__(parent)

        self.setTitle(self.tr("Downloading catalog"))
        self.setCommitPage(True)

        layout: QVBoxLayout = QVBoxLayout(self)
        self._downloader: Downloader | None = None
        self._state_queue: Queue[tuple[int, int]] = Queue()

        self._existing_catalog: Catalog | None = existing_catalog

        self._progress_bar: QProgressBar = QProgressBar(self)
        self._progress_bar.setFormat(
            self.tr(
                "%p% (%v out of %m)",
                "%p = the percentage. %v = the current value. %m = the total number of steps.",
            )
        )
        layout.addWidget(self._progress_bar)

        self._timer: QTimer = QTimer(self)
        self._timer.timeout.connect(self._on_timeout)

    def initializePage(self) -> None:
        super(ProgressPage, self).initializePage()
        self.setButtonText(QWizard.WizardButton.CommitButton, self.buttonText(QWizard.WizardButton.NextButton))

        frequency_limits: tuple[float, float] = (
            self.field("min_frequency"),
            self.field("max_frequency"),
        )
        self._downloader = Downloader(
            frequency_limits=frequency_limits,
            state_queue=self._state_queue,
            existing_catalog=self._existing_catalog,
        )
        self._downloader.start()
        self._progress_bar.setMaximum(0)
        self._timer.start(100)

    @Slot()
    def _on_timeout(self) -> None:
        cataloged_species: int
        not_yet_processed_species: int
        while not self._state_queue.empty():
            cataloged_species, not_yet_processed_species = self._state_queue.get(block=False)
            self._progress_bar.setValue(cataloged_species)
            self._progress_bar.setMaximum(cataloged_species + not_yet_processed_species)
        if self.isComplete():
            self.stop()
            self._timer.stop()
            cast(SaveCatalogWizard, self.wizard()).catalog = self._downloader.catalog
            self.completeChanged.emit()

    def isActive(self) -> bool:
        return self._downloader is not None and self._downloader.is_alive()

    def isComplete(self) -> bool:
        return self._downloader is not None and not self._downloader.is_alive()

    def stop(self) -> None:
        self._downloader.stop()
        cataloged_species: int
        not_yet_processed_species: int
        while not self._state_queue.empty():
            cataloged_species, not_yet_processed_species = self._state_queue.get(block=False)
            self._progress_bar.setValue(cataloged_species)
            self._progress_bar.setMaximum(cataloged_species + not_yet_processed_species)
        self._downloader.join()
