# coding=utf-8
from __future__ import annotations

import site
import sys
from typing import cast

from qtpy.QtGui import QTextDocument
from qtpy.QtWidgets import QGridLayout, QLabel, QMessageBox, QTabWidget, QTextBrowser, QWidget, QWidgetItem

__all__ = ["AboutBox", "about"]


class AboutBox(QMessageBox):
    def __init__(self, parent: QWidget | None = None, title: str = "", text: str = "") -> None:
        super().__init__(parent)

        if text or title:
            self.setText(text)
            self.setWindowTitle(title)

        self.setIcon(QMessageBox.Icon.Information)

        layout: QGridLayout = self.layout()

        def find_widget(name: str) -> QWidget | None:
            for i in range(layout.count()):
                widget: QWidget | None = cast(QWidgetItem, layout.itemAt(i)).widget()
                if widget is not None and widget.objectName() == name:
                    return widget

        icon_label: QLabel | None = find_widget("qt_msgboxex_icon_label")
        text_label: QLabel | None = find_widget("qt_msgbox_label")

        if parent is not None and icon_label is not None:
            icon_label.setPixmap(parent.windowIcon().pixmap(icon_label.size()))

        if text_label is not None:
            from ..utils import p_tag, tag

            text_label.hide()

            about_text: QTextBrowser = QTextBrowser(self)
            about_text.setText(text)
            cast(QTextDocument, about_text.document()).adjustSize()
            about_text.setMinimumSize(cast(QTextDocument, about_text.document()).size().toSize())

            tabs: QTabWidget = QTabWidget(self)
            tabs.setTabBarAutoHide(True)
            tabs.setTabPosition(QTabWidget.TabPosition.South)
            tabs.addTab(about_text, self.tr("About"))

            third_party_modules: list[str] = []
            prefixes: list[str] = site.getsitepackages([sys.exec_prefix, sys.prefix])
            for module_name, module in sys.modules.copy().items():
                paths = getattr(module, "__path__", [])
                if (
                    "." not in module_name
                    and module_name != "_distutils_hack"
                    and paths
                    and getattr(module, "__package__", "")
                    and any(p.startswith(prefix) for p in paths for prefix in prefixes)
                ):
                    third_party_modules.append(module_name)
            if third_party_modules:
                lines: list[str] = [
                    self.tr("The app uses the following third-party modules:"),
                    tag(
                        "ul",
                        "".join(
                            map(
                                lambda s: tag("li", tag("tt", s)),
                                sorted(third_party_modules, key=str.casefold),
                            )
                        ),
                    ),
                ]
                third_party_label: QTextBrowser = QTextBrowser(self)
                third_party_label.setText(tag("html", "".join(map(p_tag, lines))))
                tabs.addTab(third_party_label, "Third-Party")
                layout.addWidget(tabs, 0, 2, 1, 1)


def about(parent: QWidget | None = None, title: str = "", text: str = "") -> int:
    box: AboutBox = AboutBox(parent=parent, title=title, text=text)
    return box.exec()
