# -*- coding: utf-8 -*-
from __future__ import annotations

from os import PathLike

from qtpy import QT5
from qtpy.QtWidgets import QWidget

from .waiting_screen import WaitingScreen
from ..catalog import CatalogType
from ..utils import save_catalog_to_file

__all__ = ["SaveCatalogWaitingScreen"]


class SaveCatalogWaitingScreen(WaitingScreen):
    def __init__(
        self,
        parent: QWidget,
        *,
        filename: str | PathLike[str],
        catalog: CatalogType,
        frequency_limits: tuple[float, float],
        margins: float | None = None,
    ) -> None:
        if QT5:
            super(QWidget, self).__init__(parent)
        super().__init__(
            parent,
            label=self.tr("Please wait…"),
            target=save_catalog_to_file,
            kwargs=dict(filename=filename, catalog=catalog, frequency_limits=frequency_limits),
            margins=margins,
        )
