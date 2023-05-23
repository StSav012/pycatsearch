# -*- coding: utf-8 -*-
import sys

from qtpy.QtWidgets import QApplication

from ..catalog import Catalog
from .ui import UI

__all__ = ['UI', 'run']


def run() -> int:
    app: QApplication = QApplication(sys.argv)
    window: UI = UI(Catalog(*sys.argv[1:]))
    window.show()
    return app.exec()
