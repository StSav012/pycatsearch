# -*- coding: utf-8 -*-
from __future__ import annotations

from qtpy.QtWidgets import QWidget

from .selectable_label import SelectableLabel

__all__ = ["URLLabel"]


class URLLabel(SelectableLabel):
    """A label with selectable hyperlink"""

    def __init__(self, url: str, text: str, parent: QWidget | None = None) -> None:
        super().__init__(f'<a href="{url}">{text}</a>', parent)
        self.setOpenExternalLinks(True)
        self.setToolTip(url)
