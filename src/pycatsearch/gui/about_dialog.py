import site
import sys
from pathlib import Path
from typing import cast

from qtpy.QtCore import Qt
from qtpy.QtGui import QTextDocument
from qtpy.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QGridLayout,
    QLabel,
    QStyle,
    QTabWidget,
    QTextBrowser,
    QWidget,
)

from ..utils import p_tag, tag

__all__ = ["AboutBox", "about"]


class AboutBox(QDialog):
    def __init__(self, parent: QWidget | None = None, title: str = "", text: str = "") -> None:
        super().__init__(parent)

        if title:
            self.setWindowTitle(title)

        grid: QGridLayout = QGridLayout()
        self.setLayout(grid)

        has_icon: bool = False

        if parent is not None:
            icon_label: QLabel = QLabel(self)
            icon_label.setPixmap(parent.windowIcon().pixmap(8 * self.fontMetrics().xHeight()))
            grid.addWidget(icon_label, 0, 0)
            grid.setAlignment(icon_label, Qt.AlignmentFlag.AlignTop)
            margin: int = 2 * self.fontMetrics().averageCharWidth()
            icon_label.setContentsMargins(margin, margin, margin, margin)
            has_icon = True

        about_text: QTextBrowser = QTextBrowser(self)
        about_text.setText(text)
        cast(QTextDocument, about_text.document()).adjustSize()
        about_text.setMinimumSize(cast(QTextDocument, about_text.document()).size().toSize())

        tabs: QTabWidget = QTabWidget(self)
        tabs.setTabBarAutoHide(True)
        tabs.setTabPosition(QTabWidget.TabPosition.South)
        tabs.addTab(about_text, self.tr("About"))

        third_party_modules: list[str] = []
        prefixes: list[Path] = [
            Path(prefix).resolve() for prefix in site.getsitepackages([sys.exec_prefix, sys.prefix])
        ]
        for module_name, module in sys.modules.copy().items():
            paths = getattr(module, "__path__", [])
            if (
                "." not in module_name
                and module_name != "_distutils_hack"
                and paths
                and getattr(module, "__package__", "")
                and any(prefix in Path(p).resolve().parents for p in paths for prefix in prefixes)
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
        grid.addWidget(tabs, 0, 1 if has_icon else 0, 1, 1)

        button_box: QDialogButtonBox = QDialogButtonBox(self)
        button_box.setCenterButtons(
            bool(self.style().styleHint(QStyle.StyleHint.SH_MessageBox_CenterButtons, None, self))
        )
        button_box.setStandardButtons(QDialogButtonBox.StandardButton.Ok)
        button_box.button(QDialogButtonBox.StandardButton.Ok).clicked.connect(self.close)
        grid.addWidget(button_box, 1, 1 if has_icon else 0, 1, 2 if has_icon else 1)


def about(parent: QWidget | None = None, title: str = "", text: str = "") -> int:
    box: AboutBox = AboutBox(parent=parent, title=title, text=text)
    return box.exec()
