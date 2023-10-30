# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Sequence

from qtpy.QtWidgets import QAbstractScrollArea, QLabel, QListWidget, QVBoxLayout, QWidget

__all__ = ["TitledListWidget"]


class TitledListWidget(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout: QVBoxLayout = QVBoxLayout(self)
        self._title_label: QLabel = QLabel(self)
        layout.addWidget(self._title_label)
        self._list_widget: QListWidget = QListWidget(self)
        self._list_widget.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
        layout.addWidget(self._list_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setStretch(0, 0)

    def setTitle(self, title: str) -> None:
        self._title_label.setText(title)

    def addItems(self, labels: Sequence[str]) -> None:
        self._list_widget.addItems(labels)
