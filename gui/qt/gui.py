# coding: utf-8

from contextlib import suppress

__all__ = ['QAction', 'QAbstractTextDocumentLayout', 'QClipboard', 'QCloseEvent', 'QIcon', 'QPainter', 'QPixmap',
           'QScreen', 'QTextDocument', 'QValidator']

while True:
    with suppress(ImportError, ModuleNotFoundError):
        from PySide6.QtGui import (QAction, QAbstractTextDocumentLayout, QClipboard, QCloseEvent, QIcon, QPainter,
                                   QPixmap, QScreen, QTextDocument, QValidator)

        break
    with suppress(ImportError, ModuleNotFoundError):
        from PyQt5.QtWidgets import QAction
        from PyQt5.QtGui import (QAbstractTextDocumentLayout, QClipboard, QCloseEvent, QIcon, QPainter, QPixmap,
                                 QScreen, QTextDocument, QValidator)

        break
    with suppress(ImportError, ModuleNotFoundError):
        from PyQt6.QtGui import (QAction, QAbstractTextDocumentLayout, QClipboard, QCloseEvent, QIcon, QPainter, QPixmap,
                                 QScreen, QTextDocument, QValidator)

        break
    with suppress(ImportError, ModuleNotFoundError):
        from PySide2.QtWidgets import QAction
        from PySide2.QtGui import (QAbstractTextDocumentLayout, QClipboard, QCloseEvent, QIcon, QPainter, QPixmap,
                                   QScreen, QTextDocument, QValidator)

        break
    raise ModuleNotFoundError('Cannot import QtGui from PySide6, PyQt5, PyQt6, or PySide2')
