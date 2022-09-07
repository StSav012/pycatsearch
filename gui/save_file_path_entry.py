# coding: utf-8
from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pathvalidate

from gui.qt.core import Signal
from gui.qt.widgets import QFileDialog, QHBoxLayout, QLabel, QLineEdit, QStyle, QToolButton, QWidget

_all__ = ['SaveFilePathEntry']


class SaveFilePathEntry(QWidget):
    pathChanged: Signal = Signal(name='pathChanged')

    def __init__(self, initial_file_path: str = '',
                 filters: str | Iterable[str] = '', initial_filter: str = '',
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._path: Path | None = None
        self.filters: str | list[str] = [filters] if isinstance(filters, str) else list(filters)
        self.initial_filter: str = initial_filter or self.filters[0]

        layout: QHBoxLayout = QHBoxLayout()
        self.setLayout(layout)

        self._status: QLabel = QLabel(self)
        layout.addWidget(self._status)

        self._text: QLineEdit = QLineEdit(self)
        self._text.setText(initial_file_path)
        self.on_text_changed(initial_file_path)  # call manually to handle empty `initial_file_path`
        self._text.textChanged.connect(self.on_text_changed)
        layout.addWidget(self._text)

        browse_button: QToolButton = QToolButton(self)
        browse_button.setText(self.tr('Browse...'))
        browse_button.clicked.connect(self.on_browse_button_clicked)
        layout.addWidget(browse_button)

        layout.setStretch(1, 0)
        layout.setStretch(2, 0)
        layout.setContentsMargins(0, 0, 0, 0)

    @property
    def path(self) -> Path | None:
        return self._path

    @path.setter
    def path(self, new_path: str | Path | None) -> None:
        if isinstance(new_path, str):
            self._path = Path(new_path).resolve()
        else:
            self._path = new_path
        self.pathChanged.emit()

    def on_text_changed(self, text: str) -> None:
        """ display an icon showing whether the entered file name is acceptable """

        self._text.setToolTip(text)

        if not text:
            self._status.setPixmap(self.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxCritical)
                                   .pixmap(self._text.height()))
            self._status.setVisible(True)
            self.path = None
            return

        path: Path = Path(text).resolve()

        if path.is_dir():
            self._status.setPixmap(self.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxCritical)
                                   .pixmap(self._text.height()))
            self._status.setVisible(True)
            self.path = None
            return
        if path.exists():
            self._status.setPixmap(self.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxWarning)
                                   .pixmap(self._text.height()))
            self._status.setVisible(True)
            self.path = path
            return
        try:
            pathvalidate.validate_filepath(path, platform='auto')
        except pathvalidate.error.ValidationError as ex:
            print(ex.description)
            self._status.setPixmap(self.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxCritical)
                                   .pixmap(self._text.height()))
            self._status.setVisible(True)
            self.path = None
        else:
            self._status.clear()
            self._status.setVisible(False)
            self.path = path

    def on_browse_button_clicked(self) -> None:
        new_file_name: str
        new_file_name, _ = QFileDialog.getSaveFileName(
            self, self.tr('Save As...'),
            str(self.path or ''),
            ';;'.join(self.filters), self.initial_filter)
        if new_file_name:
            self._text.setText(new_file_name)
