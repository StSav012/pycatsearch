# -*- coding: utf-8 -*-
import sys

from PyQt5.QtWidgets import QApplication

from catalog import Catalog
from gui._ui import UI


def run() -> None:
    app: QApplication = QApplication(sys.argv)
    window: UI = UI(Catalog(*sys.argv[1:]))
    window.show()
    app.exec()


if __name__ == '__main__':
    run()
