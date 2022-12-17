# -*- coding: utf-8 -*-
import sys

from qtpy.QtWidgets import QApplication

from catalog import Catalog
from gui.ui import UI

__all__ = ['UI', 'run']


def run() -> None:
    app: QApplication = QApplication(sys.argv)
    window: UI = UI(Catalog(*sys.argv[1:]))
    window.show()
    if hasattr(QApplication, 'exec'):
        sys.exit(app.exec())
    else:
        sys.exit(app.exec_())


if __name__ == '__main__':
    run()
