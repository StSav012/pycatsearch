# -*- coding: utf-8 -*-
import sys

from PyQt5.QtWidgets import QApplication

from catalog import Catalog
from gui.ui import UI

__all__ = ['UI', 'run']


def run() -> None:
    app: QApplication = QApplication(sys.argv)
    window: UI = UI(Catalog(*sys.argv[1:]))
    window.show()
    app.exec()


if __name__ == '__main__':
    run()
