# -*- coding: utf-8 -*-
from __future__ import annotations

from qtpy.QtCore import Qt
from qtpy.QtWidgets import QLabel, QWidget

__all__ = ["SelectableLabel"]


class SelectableLabel(QLabel):
    """A label with selectable text"""

    def __init__(self, text: str, parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
