# coding: utf-8

from contextlib import suppress

__all__ = ['QAbstractTableModel', 'QJsonDocument', 'QMimeData', 'QModelIndex', 'QPoint', 'QPointF', 'QRect',
           'QSettings', 'QSize', 'QTimer', 'Qt', 'Signal', 'qCompress']

while True:
    with suppress(ImportError, ModuleNotFoundError):
        from PySide6.QtCore import (QAbstractTableModel, QJsonDocument, QMimeData, QModelIndex, QPoint, QPointF, QRect,
                                    QSettings, QSize, QTimer, Qt, Signal, qCompress)
        break
    with suppress(ImportError, ModuleNotFoundError):
        from PyQt5.QtCore import (QAbstractTableModel, QJsonDocument, QMimeData, QModelIndex, QPoint, QPointF, QRect,
                                  QSettings, QSize, QTimer, Qt, pyqtSignal as Signal, qCompress)
        break
    with suppress(ImportError, ModuleNotFoundError):
        from PyQt6.QtCore import (QAbstractTableModel, QJsonDocument, QMimeData, QModelIndex, QPoint, QPointF, QRect,
                                  QSettings, QSize, QTimer, Qt, pyqtSignal as Signal, qCompress)
        break
    with suppress(ImportError, ModuleNotFoundError):
        from PySide2.QtCore import (QAbstractTableModel, QJsonDocument, QMimeData, QModelIndex, QPoint, QPointF, QRect,
                                    QSettings, QSize, QTimer, Qt, Signal, qCompress)
        break
    raise ModuleNotFoundError('Cannot import QtCore from PySide6, PyQt5, PyQt6, or PySide2')
