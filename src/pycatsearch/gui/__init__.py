# -*- coding: utf-8 -*-
from __future__ import annotations

import sys
from contextlib import suppress
from datetime import datetime, timedelta, timezone
from functools import partialmethod
from os import PathLike
from pathlib import Path
from typing import Any, AnyStr

from qtpy import PYSIDE2, QT6
from qtpy.QtCore import QLibraryInfo, QLocale, QTranslator, Qt, qVersion
from qtpy.QtGui import QIcon
from qtpy.QtWidgets import QAbstractSpinBox, QApplication, QDialog, QMenu

__all__ = ["qta_icon", "run"]


def _version_tuple(version_string: AnyStr) -> tuple[int | AnyStr, ...]:
    result: tuple[int | AnyStr, ...] = tuple()
    part: AnyStr
    for part in version_string.split("." if isinstance(version_string, str) else b"."):
        try:
            result += (int(part),)
        except ValueError:
            # follow `pkg_resources` version 0.6a9: remove dashes to sort letters after digits
            result += (part.replace("-", ""),) if isinstance(part, str) else (part.replace(b"-", b""),)
    return result


def _warn_about_outdated_package(package_name: str, package_version: str, release_time: datetime) -> None:
    """Display a warning about an outdated package a year after the package released"""
    if datetime.now(tz=timezone.utc) - release_time > timedelta(days=366):
        import tkinter.messagebox

        tkinter.messagebox.showwarning(
            title="Package Outdated", message=f"Please update {package_name} package to {package_version} or newer"
        )


def _make_old_qt_compatible_again() -> None:
    def to_iso_format(s: str) -> str:
        if sys.version_info < (3, 11):
            import re
            from typing import Callable

            if s.endswith("Z"):
                # '2011-11-04T00:05:23Z'
                s = s[:-1] + "+00:00"

            def from_iso_datetime(m: re.Match[str]) -> str:
                groups: dict[str, str] = m.groupdict("")
                date: str = f"{m['year']}-{m['month']}-{m['day']}"
                time: str = (
                    f"{groups['hour']:0>2}:{groups['minute']:0>2}:{groups['second']:0>2}.{groups['fraction']:0<6}"
                )
                return date + "T" + time + groups["offset"]

            def from_iso_calendar(m: re.Match[str]) -> str:
                from datetime import date

                groups: dict[str, str] = m.groupdict("")
                date: str = date.fromisocalendar(
                    year=int(m["year"]), week=int(m["week"]), day=int(m["dof"])
                ).isoformat()
                time: str = (
                    f"{groups['hour']:0>2}:{groups['minute']:0>2}:{groups['second']:0>2}.{groups['fraction']:0<6}"
                )
                return date + "T" + time + groups["offset"]

            patterns: dict[str, Callable[[re.Match[str]], str]] = {
                # '20111104', '20111104T000523283'
                r"(?P<year>\d{4})(?P<month>\d{2})(?P<day>\d{2})"
                r"(.(?P<hour>\d{2})(?P<minute>\d{2})(?P<second>\d{2})(?P<fraction>\d+)?)?"
                r"(?P<offset>[+\-].+)?": from_iso_datetime,
                # '2011-11-04', '2011-11-04T00:05:23.283', '2011-11-04T00:05:23.283+00:00'
                r"(?P<year>\d{4})-(?P<month>\d{1,2})-(?P<day>\d{1,2})"
                r"(.(?P<hour>\d{1,2}):(?P<minute>\d{1,2}):(?P<second>\d{1,2})(\.(?P<fraction>\d+))?)?"
                r"(?P<offset>[+\-].+)?": from_iso_datetime,
                # '2011-W01-2T00:05:23.283'
                r"(?P<year>\d{4})-W(?P<week>\d{1,2})-(?P<dof>\d{1,2})"
                r"(.(?P<hour>\d{1,2}):(?P<minute>\d{1,2}):(?P<second>\d{1,2})(\.(?P<fraction>\d+))?)?"
                r"(?P<offset>[+\-].+)?": from_iso_calendar,
                # '2011W0102T000523283'
                r"(?P<year>\d{4})-W(?P<week>\d{2})-(?P<dof>\d{2})"
                r"(.(?P<hour>\d{1,2})(?P<minute>\d{1,2})(?P<second>\d{1,2})(?P<fraction>\d+)?)?"
                r"(?P<offset>[+\-].+)?": from_iso_calendar,
            }
            match: re.Match[str] | None
            for p in patterns:
                match = re.fullmatch(p, s)
                if match is not None:
                    s = patterns[p](match)
                    break

        return s

    if not QT6:
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling)
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)

    from qtpy import __version__

    if _version_tuple(__version__) < _version_tuple("2.3.1"):
        _warn_about_outdated_package(
            package_name="QtPy",
            package_version="2.3.1",
            release_time=datetime.fromisoformat(to_iso_format("2023-03-28T23:06:05Z")),
        )
        if QT6:
            QLibraryInfo.LibraryLocation = QLibraryInfo.LibraryPath
    if _version_tuple(__version__) < _version_tuple("2.4.0"):
        _warn_about_outdated_package(
            package_name="QtPy",
            package_version="2.4.0",
            release_time=datetime.fromisoformat(to_iso_format("2023-08-29T16:24:56Z")),
        )
        if PYSIDE2:
            QApplication.exec = QApplication.exec_
            QDialog.exec = QDialog.exec_
            QMenu.exec = lambda self, pos: self.exec_(pos)

        if not QT6:
            QLibraryInfo.path = lambda *args, **kwargs: QLibraryInfo.location(*args, **kwargs)
            QLibraryInfo.LibraryPath = QLibraryInfo.LibraryLocation

        if _version_tuple(qVersion()) < _version_tuple("6.3"):
            from qtpy.QtCore import QObject
            from qtpy.QtGui import QKeySequence
            from qtpy.QtWidgets import QAction, QToolBar, QWidget

            def add_action(self: QWidget, *args, old_add_action) -> QAction:
                action: QAction
                icon: QIcon
                text: str
                shortcut: QKeySequence | QKeySequence.StandardKey | str | int
                receiver: QObject
                member: bytes
                if all(
                    isinstance(arg, t)
                    for arg, t in zip(args, [str, (QKeySequence, QKeySequence.StandardKey, str, int), QObject, bytes])
                ):
                    if len(args) == 2:
                        text, shortcut = args
                        action = old_add_action(self, text)
                        action.setShortcut(shortcut)
                    elif len(args) == 3:
                        text, shortcut, receiver = args
                        action = old_add_action(self, text, receiver)
                        action.setShortcut(shortcut)
                    elif len(args) == 4:
                        text, shortcut, receiver, member = args
                        action = old_add_action(self, text, receiver, member, shortcut)
                    else:
                        return old_add_action(self, *args)
                    return action
                elif all(
                    isinstance(arg, t)
                    for arg, t in zip(
                        args, [QIcon, str, (QKeySequence, QKeySequence.StandardKey, str, int), QObject, bytes]
                    )
                ):
                    if len(args) == 3:
                        icon, text, shortcut = args
                        action = old_add_action(self, icon, text)
                        action.setShortcut(QKeySequence(shortcut))
                    elif len(args) == 4:
                        icon, text, shortcut, receiver = args
                        action = old_add_action(self, icon, text, receiver)
                        action.setShortcut(QKeySequence(shortcut))
                    elif len(args) == 5:
                        icon, text, shortcut, receiver, member = args
                        action = old_add_action(self, icon, text, receiver, member, QKeySequence(shortcut))
                    else:
                        return old_add_action(self, *args)
                    return action
                return old_add_action(self, *args)

            QMenu.addAction = partialmethod(add_action, old_add_action=QMenu.addAction)
            QToolBar.addAction = partialmethod(add_action, old_add_action=QToolBar.addAction)
    if _version_tuple(__version__) < _version_tuple("2.4.1"):
        _warn_about_outdated_package(
            package_name="QtPy",
            package_version="2.4.1",
            release_time=datetime.fromisoformat(to_iso_format("2023-10-23T23:57:23Z")),
        )

    # not a part of any QtPy (yet)
    if PYSIDE2:
        # noinspection PyUnresolvedReferences
        QAbstractSpinBox.setAlignment = partialmethod(
            lambda self, flag, _old: _old(self, Qt.Alignment(flag)),
            _old=QAbstractSpinBox.setAlignment,
        )
        Qt.AlignmentFlag.__or__ = lambda self, other: int(self) | int(other)
        Qt.AlignmentFlag.__ror__ = lambda self, other: int(other) | int(self)


def qta_icon(*qta_name: str, **qta_specs: Any) -> QIcon:
    if qta_name:
        with suppress(ImportError, Exception):
            from qtawesome import icon

            return icon(*qta_name, **qta_specs)  # might raise an `Exception` if the icon is not in the font

    return QIcon()


def run(*catalogs: str | PathLike[str]) -> int:
    import re

    # fix `re.RegexFlag.NOFLAG` missing on some systems
    if not hasattr(re.RegexFlag, "NOFLAG"):
        re.RegexFlag.NOFLAG = 0

    _make_old_qt_compatible_again()

    from .ui import UI
    from ..catalog import Catalog

    app: QApplication = QApplication(sys.argv)

    languages: set[str] = set(QLocale().uiLanguages() + [QLocale().bcp47Name(), QLocale().name()])
    language: str
    translations_path: str = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
    qt_translator: QTranslator = QTranslator()
    for language in languages:
        if qt_translator.load("qt_" + language, translations_path):
            QApplication.installTranslator(qt_translator)
            break
    qtbase_translator: QTranslator = QTranslator()
    for language in languages:
        if qtbase_translator.load("qtbase_" + language, translations_path):
            QApplication.installTranslator(qtbase_translator)
            break
    my_translator: QTranslator = QTranslator()
    for language in languages:
        if my_translator.load(language, str(Path(__file__).parent / "i18n")):
            QApplication.installTranslator(my_translator)
            break

    window: UI = UI(Catalog(*catalogs))
    window.show()
    return app.exec()
