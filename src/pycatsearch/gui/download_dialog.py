# -*- coding: utf-8 -*-
from __future__ import annotations

from math import inf
from queue import Queue
from typing import cast

from qtpy.QtCore import QTimer
from qtpy.QtWidgets import (QDialog, QDoubleSpinBox, QFormLayout, QLabel, QProgressBar, QVBoxLayout,
                            QWidget, QWizard, QWizardPage)
from qtpy.compat import getsavefilename

try:
    from ..async_downloader import Downloader
except (SyntaxError, ImportError, ModuleNotFoundError):
    from ..downloader import Downloader
from .waiting_screen import WaitingScreen
from ..utils import all_cases, ensure_prefix, save_catalog_to_file


__all__ = ['DownloadDialog']


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

        try:  # PyQt*
            self.registerField('min_frequency', self.spin_min_frequency,
                               'value', self.spin_min_frequency.valueChanged)
            self.registerField('max_frequency', self.spin_max_frequency,
                               'value', self.spin_max_frequency.valueChanged)
        except TypeError:  # PySide*
            self.registerField('min_frequency', self.spin_min_frequency,
                               'value', 'self.spin_min_frequency.valueChanged')
            self.registerField('max_frequency', self.spin_max_frequency,
                               'value', 'self.spin_max_frequency.valueChanged')

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

    def validatePage(self) -> bool:
        return self.spin_max_frequency.value() > self.spin_min_frequency.value()


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
        self.setButtonText(QWizard.WizardButton.CommitButton, self.tr('&Start'))
        self._label.setText(self.tr('Click {button_text} to start the download data'
                                    ' for {min_frequency} to {max_frequency} MHz.')
                            .format(button_text=self.buttonText(QWizard.WizardButton.CommitButton).replace('&', ''),
                                    min_frequency=self.field('min_frequency'),
                                    max_frequency=self.field('max_frequency')))


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
        if self.isComplete():
            self.timer.stop()
            self.wizard().catalog = self.downloader.catalog
            self.completeChanged.emit()

    def isComplete(self) -> bool:
        return self.downloader is not None and not self.downloader.is_alive()


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
            self.setButtonText(QWizard.WizardButton.FinishButton, self.tr('&Save'))
            self._label.setText(
                self.tr('Click {button_text} to save the catalog'
                        ' for {min_frequency} to {max_frequency} MHz.')
                .format(button_text=self.buttonText(QWizard.WizardButton.FinishButton).replace('&', ''),
                        min_frequency=self.field('min_frequency'),
                        max_frequency=self.field('max_frequency')))
        else:
            self.setTitle(self.tr('Failure'))
            self._label.setText(self.tr('For the specified frequency range, nothing has been loaded.'))


class DownloadDialog(QWizard):
    """ GUI for `async_downloader.Downloader` """

    def __init__(self, frequency_limits: tuple[float, float] = (-inf, inf),
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)

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

    def _get_save_file_name(self, formats: dict[tuple[str, ...], str],
                            caption: str = '', directory: str = '') -> tuple[str, str]:

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
                                            caption=caption,
                                            filters=join_file_dialog_formats(formats),
                                            basedir=directory)
        return filename, _filter

    def done(self, exit_code: QDialog.DialogCode) -> None:
        if self.progress_page.downloader is not None and self.progress_page.downloader.is_alive():
            self.progress_page.downloader.join(0.1)

        if exit_code == QDialog.DialogCode.Accepted and self.catalog:
            _formats: dict[tuple[str, ...], str] = {
                tuple(all_cases('.json.gz')): self.tr('JSON with GZip compression', 'file type'),
                tuple(all_cases('.json.bz2')): self.tr('JSON with Bzip2 compression', 'file type'),
                tuple(*all_cases('.json.xz'), *all_cases('.json.lzma')):
                    self.tr('JSON with LZMA2 compression', 'file type'),
                tuple(all_cases('.json')): self.tr('JSON', 'file type'),
            }
            save_file_name: str
            save_file_name, _ = self._get_save_file_name(formats=_formats, caption=self.tr('Save As...'))
            if not save_file_name:
                return

            ws: WaitingScreen = WaitingScreen(
                self,
                label=self.tr('Please wait...'),
                target=save_catalog_to_file,
                kwargs={
                    'filename': save_file_name,
                    'catalog': self.catalog,
                    'frequency_limits': (self.field('min_frequency'), self.field('max_frequency'))
                })
            ws.exec()

        super(DownloadDialog, self).done(exit_code)
