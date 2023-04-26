# -*- coding: utf-8 -*-
import sys

from qtpy.QtWidgets import QApplication

from ..catalog import Catalog
from .ui import UI

__all__ = ['UI', 'run']


def run() -> None:
    app: QApplication = QApplication(sys.argv)
    window: UI = UI(Catalog(*sys.argv[1:]))
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    run()
