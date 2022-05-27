# -*- coding: utf-8 -*-
from __future__ import annotations

import gzip
import json
from math import inf
from pathlib import Path
from queue import Queue
from typing import BinaryIO, TextIO, cast

from PyQt5.QtCore import QJsonDocument, QTimer, Qt, qCompress
from PyQt5.QtWidgets import (QDoubleSpinBox, QFormLayout, QLabel, QProgressBar, QVBoxLayout, QWidget, QWizard,
                             QWizardPage)

from async_downloader import Downloader
from gui.save_file_path_entry import SaveFilePathEntry

__all__ = ['DownloadDialog']

from utils import CATALOG, FREQUENCY


class SettingsPage(QWizardPage):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.setTitle(self.tr('New catalog'))

        layout: QFormLayout = QFormLayout(self)

        self.spin_min_frequency: QDoubleSpinBox = QDoubleSpinBox(self)
        self.spin_max_frequency: QDoubleSpinBox = QDoubleSpinBox(self)
        self.spin_min_frequency.setRange(0., inf)
        self.spin_max_frequency.setRange(0., inf)
        self.spin_min_frequency.valueChanged.connect(self.spin_max_frequency.setMinimum)
        self.spin_max_frequency.valueChanged.connect(self.spin_min_frequency.setMaximum)
        self.spin_min_frequency.setPrefix(self.tr('', 'spin prefix'))
        self.spin_max_frequency.setPrefix(self.tr('', 'spin prefix'))
        self.spin_min_frequency.setSuffix(self.tr(' MHz', 'spin suffix'))
        self.spin_max_frequency.setSuffix(self.tr(' MHz', 'spin suffix'))
        layout.addRow(self.tr('Minimal frequency:'), self.spin_min_frequency)
        layout.addRow(self.tr('Maximal frequency:'), self.spin_max_frequency)

        filters: tuple[str, ...] = (
            f"{self.tr('JSON')} (*.json)",
            f"{self.tr('GZipped JSON')} (*.json.gz)",
            f"{self.tr('Binary Qt JSON')} (*.qb""json *.qb""js)",
            f"{self.tr('Compressed Binary Qt JSON')} (*.qb""jsz)",
        )
        self.path_entry: SaveFilePathEntry = SaveFilePathEntry(filters=filters, initial_filter=filters[1])
        self.path_entry.pathChanged.connect(self.completeChanged.emit)
        layout.addRow(self.tr('Save catalog to'), self.path_entry)

        self.registerField('min_frequency', self.spin_min_frequency, 'value', self.spin_min_frequency.valueChanged)
        self.registerField('max_frequency', self.spin_max_frequency, 'value', self.spin_max_frequency.valueChanged)

    @property
    def frequency_limits(self) -> tuple[float, float]:
        return self.spin_min_frequency.value(), self.spin_max_frequency.value()

    @frequency_limits.setter
    def frequency_limits(self, new_limits: tuple[float, float]) -> None:
        min_frequency: float = min(new_limits)
        max_frequency: float = max(new_limits)
        self.spin_max_frequency.setMaximum(max(2.0 * max_frequency, self.spin_max_frequency.maximum()))
        if min_frequency > self.spin_max_frequency.value():
            self.spin_max_frequency.setValue(max_frequency)
            self.spin_min_frequency.setValue(min_frequency)
        else:
            self.spin_min_frequency.setValue(min_frequency)
            self.spin_max_frequency.setValue(max_frequency)

    def isComplete(self) -> bool:
        return self.path_entry.path is not None

    def validatePage(self) -> bool:
        return self.spin_max_frequency.value() > self.spin_min_frequency.value() and self.path_entry.path is not None


class DownloadConfirmationPage(QWizardPage):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.setTitle(self.tr('Downloading catalog'))
        self.setCommitPage(True)

        layout: QVBoxLayout = QVBoxLayout(self)
        self._label: QLabel = QLabel(self)
        layout.addWidget(self._label)

    def initializePage(self) -> None:
        super(DownloadConfirmationPage, self).initializePage()
        self.setButtonText(QWizard.WizardButton.CommitButton, self.tr('Start'))
        self._label.setText(self.tr('Click {} to start the download')
                            .format(self.buttonText(QWizard.WizardButton.CommitButton).replace('&', '')))


class ProgressPage(QWizardPage):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.setTitle(self.tr('Downloading catalog'))
        self.setCommitPage(True)

        layout: QVBoxLayout = QVBoxLayout(self)
        self.downloader: Downloader | None = None
        self.state_queue: Queue[tuple[int, int]] = Queue()

        self.progress_bar: QProgressBar = QProgressBar(self)
        layout.addWidget(self.progress_bar)

        self.timer: QTimer = QTimer(self)
        self.timer.timeout.connect(self.on_timeout)

    def initializePage(self) -> None:
        super(ProgressPage, self).initializePage()
        self.setButtonText(QWizard.WizardButton.CommitButton, self.buttonText(QWizard.WizardButton.NextButton))

        frequency_limits: tuple[float, float] = (
            self.field('min_frequency'),
            self.field('max_frequency'),
        )
        self.downloader = Downloader(frequency_limits=frequency_limits, state_queue=self.state_queue)
        self.downloader.start()
        self.timer.start(100)

    def on_timeout(self) -> None:
        while not self.state_queue.empty():
            cataloged_species: int
            not_yet_processed_species: int
            cataloged_species, not_yet_processed_species = self.state_queue.get(block=False)
            self.progress_bar.setValue(cataloged_species)
            self.progress_bar.setMaximum(cataloged_species + not_yet_processed_species)
        if not self.downloader.is_alive():
            self.timer.stop()
            self.completeChanged.emit()

    def isComplete(self) -> bool:
        self.wizard().catalog = self.downloader.catalog
        return not self.downloader.is_alive()


class SummaryPage(QWizardPage):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout: QVBoxLayout = QVBoxLayout(self)
        self._label: QLabel = QLabel(self)
        layout.addWidget(self._label)

    def initializePage(self) -> None:
        super(SummaryPage, self).initializePage()
        if cast(DownloadDialog, self.wizard()).catalog:
            self.setTitle(self.tr('Success'))
            self.setButtonText(QWizard.WizardButton.FinishButton, self.tr('Save'))
            self._label.setText(self.tr('Click {} to save the catalog into {}')
                                .format(self.buttonText(QWizard.WizardButton.FinishButton).replace('&', ''),
                                        cast(DownloadDialog, self.wizard()).settings_page.path_entry.path))
        else:
            self.setTitle(self.tr('Failure'))
            self._label.setText(self.tr('For the specified frequency range, nothing has been loaded'))


class DownloadDialog(QWizard):
    """ GUI for `async_downloader.Downloader` """

    def __init__(self, frequency_limits: tuple[float, float] = (-inf, inf),
                 parent: QWidget | None = None,
                 flags: Qt.WindowFlags = Qt.WindowFlags()) -> None:
        super().__init__(parent, flags)

        self.catalog: list[dict[str, int | str | list[dict[str, float]]]] = []

        self.setModal(True)
        self.setWindowTitle(self.tr('Download Catalog'))
        if parent is not None:
            self.setWindowIcon(parent.windowIcon())

        self.settings_page: SettingsPage = SettingsPage(self)
        self.settings_page.frequency_limits = frequency_limits
        self.addPage(self.settings_page)
        self.addPage(DownloadConfirmationPage(self))
        self.progress_page: ProgressPage = ProgressPage(self)
        self.addPage(self.progress_page)
        self.addPage(SummaryPage(self))

    def back(self) -> None:
        if self.progress_page.downloader is not None and self.progress_page.downloader.is_alive():
            self.progress_page.downloader.join(0.1)
        super(DownloadDialog, self).back()

    def next(self) -> None:
        if self.progress_page.downloader is not None and self.progress_page.downloader.is_alive():
            self.progress_page.downloader.join(0.1)
        super(DownloadDialog, self).next()

    def restart(self) -> None:
        if self.progress_page.downloader is not None and self.progress_page.downloader.is_alive():
            self.progress_page.downloader.join(0.1)
        super(DownloadDialog, self).restart()

    def done(self, exit_code: bool) -> None:
        if self.progress_page.downloader is not None and self.progress_page.downloader.is_alive():
            self.progress_page.downloader.join(0.1)
        if exit_code and self.catalog:
            saving_path: Path = self.settings_page.path_entry.path
            f: TextIO | BinaryIO | gzip.GzipFile
            if saving_path.suffix.casefold() == '.json':
                with saving_path.open('wt') as f:
                    f.write(json.dumps({
                        CATALOG: self.catalog,
                        FREQUENCY: [self.field('min_frequency'), self.field('max_frequency')]
                    }, indent=4).encode())
            elif saving_path.name.casefold().endswith('.json.gz'):
                with gzip.open(saving_path, 'wb') as f:
                    f.write(json.dumps({
                        CATALOG: self.catalog,
                        FREQUENCY: [self.field('min_frequency'), self.field('max_frequency')]
                    }, indent=4).encode())
            elif saving_path.suffix.casefold() in ('.qb''json', '.qb''js'):
                with saving_path.open('wb') as f:
                    f.write(QJsonDocument({
                        CATALOG: self.catalog,
                        FREQUENCY: [self.field('min_frequency'), self.field('max_frequency')]
                    }).toBinaryData().data())
            elif saving_path.suffix == '.qb''jsz':
                with saving_path.open('wb') as f:
                    f.write(qCompress(QJsonDocument({
                        CATALOG: self.catalog,
                        FREQUENCY: [self.field('min_frequency'), self.field('max_frequency')]
                    }).toBinaryData()).data())
            else:
                raise ValueError(f'Do not know what to save into {saving_path}')

        super(DownloadDialog, self).done(exit_code)
