# -*- coding: utf-8 -*-
import sys
from contextlib import suppress
from pathlib import Path
from typing import Any

from qtpy.QtCore import QLibraryInfo, QLocale, QTranslator
from qtpy.QtGui import QIcon
from qtpy.QtWidgets import QApplication

from .ui import UI
from ..catalog import Catalog

__all__ = ['icon', 'run']


def icon(*qta_name: str, **qta_specs: Any) -> QIcon:
    if qta_name:
        with suppress(ImportError, Exception):
            from qtawesome import icon

            return icon(*qta_name, **qta_specs)  # might raise an `Exception` if the icon is not in the font

    return QIcon()


def run() -> int:
    app: QApplication = QApplication(sys.argv)

    languages: set[str] = set(QLocale().uiLanguages() + [QLocale().bcp47Name(), QLocale().name()])
    language: str
    qt_translator: QTranslator = QTranslator()
    for language in languages:
        if qt_translator.load('qt_' + language,
                              QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)):
            QApplication.installTranslator(qt_translator)
            break
    qtbase_translator: QTranslator = QTranslator()
    for language in languages:
        if qtbase_translator.load('qtbase_' + language,
                                  QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)):
            QApplication.installTranslator(qtbase_translator)
            break
    my_translator: QTranslator = QTranslator()
    for language in languages:
        if my_translator.load(language, str(Path(__file__).parent / 'i18n')):
            QApplication.installTranslator(my_translator)
            break

    window: UI = UI(Catalog(*sys.argv[1:]))
    window.show()
    return app.exec()
