# -*- coding: utf-8 -*-
from __future__ import annotations

from qtpy.QtCore import QLocale
from qtpy.QtWidgets import QLabel, QVBoxLayout, QWidget, QWizard, QWizardPage

__all__ = ["DownloadConfirmationPage"]


class DownloadConfirmationPage(QWizardPage):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.setTitle(self.tr("Downloading catalog"))
        self.setCommitPage(True)

        layout: QVBoxLayout = QVBoxLayout(self)
        self._label: QLabel = QLabel(self)
        layout.addWidget(self._label)

    def initializePage(self) -> None:
        super(DownloadConfirmationPage, self).initializePage()
        self.setButtonText(QWizard.WizardButton.CommitButton, self.tr("&Start"))
        self._label.setText(
            self.tr(
                "Click {button_text} to start the download data for {min_frequency} to {max_frequency} MHz."
            ).format(
                button_text=self.buttonText(QWizard.WizardButton.CommitButton).replace("&", ""),
                min_frequency=QLocale().toString(self.field("min_frequency")),
                max_frequency=QLocale().toString(self.field("max_frequency")),
            )
        )
