import site
import sys
from functools import partial
from importlib.metadata import PackageNotFoundError, version
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

        third_party_modules: list[tuple[str, str]] = []
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
                try:
                    third_party_modules.append((module_name, version(module_name)))
                except PackageNotFoundError:
                    third_party_modules.append((module_name, getattr(module, "__version__", "")))
        if third_party_modules:
            td_tag: partial[str] = partial(tag, "td")
            tr_tag: partial[str] = partial(tag, "tr")
            th_tag: partial[str] = partial(tag, "th", scope="col")
            lines: list[str] = [
                self.tr("The app uses the following third-party modules:"),
                tag(
                    "table",
                    tag(
                        "thead",
                        tr_tag(th_tag(self.tr("Package Name")) + th_tag(self.tr("Package Version"))),
                    )
                    + tag(
                        "tbody",
                        "".join(
                            map(
                                lambda s: tr_tag(td_tag(tag("tt", s[0])) + td_tag(s[1], align="center")),
                                sorted(third_party_modules, key=lambda s: (s[0].casefold(), s[1])),
                            )
                        ),
                    ),
                    width="100%",
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
