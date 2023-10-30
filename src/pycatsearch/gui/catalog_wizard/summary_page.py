# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import cast

from qtpy.QtCore import QLocale
from qtpy.QtWidgets import QLabel, QVBoxLayout, QWidget, QWizard, QWizardPage

__all__ = ["SummaryPage"]


class SummaryPage(QWizardPage):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout: QVBoxLayout = QVBoxLayout(self)
        self._label: QLabel = QLabel(self)
        layout.addWidget(self._label)

    def initializePage(self) -> None:
        from . import SaveCatalogWizard

        super(SummaryPage, self).initializePage()
        if cast(SaveCatalogWizard, self.wizard()).catalog:
            self.setTitle(self.tr("Success"))
            self.setButtonText(QWizard.WizardButton.FinishButton, self.tr("&Save"))
            self._label.setText(
                self.tr("Click {button_text} to save the catalog for {min_frequency} to {max_frequency} MHz.").format(
                    button_text=self.buttonText(QWizard.WizardButton.FinishButton).replace("&", ""),
                    min_frequency=QLocale().toString(self.field("min_frequency")),
                    max_frequency=QLocale().toString(self.field("max_frequency")),
                )
            )
        else:
            self.setTitle(self.tr("Failure"))
            self._label.setText(self.tr("For the specified frequency range, nothing has been loaded."))
