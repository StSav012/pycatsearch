# -*- coding: utf-8 -*-
import sys
from contextlib import suppress
from typing import Any

from qtpy.QtGui import QIcon
from qtpy.QtWidgets import QApplication

from .ui import UI
from ..catalog import Catalog

__all__ = ['UI', 'icon', 'run']


def icon(*qta_name: str, **qta_specs: Any) -> QIcon:
    if qta_name:
        with suppress(ImportError, Exception):
            from qtawesome import icon

            return icon(*qta_name, **qta_specs)  # might raise an `Exception` if the icon is not in the font

    return QIcon()


def run() -> int:
    app: QApplication = QApplication(sys.argv)
    window: UI = UI(Catalog(*sys.argv[1:]))
    window.show()
    return app.exec()
