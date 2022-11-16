# -*- coding: utf-8 -*-
from __future__ import annotations

from threading import Thread
from typing import Any, Callable, Mapping, Sequence

from qtpy.QtCore import QCoreApplication, Qt
from qtpy.QtWidgets import QGridLayout, QLabel, QWidget

__all__ = ['WaitingScreen']


class WaitingScreen(QWidget):
    def __init__(self, parent: QWidget, label: str | QWidget,
                 target: Callable[[...], Any], args: Sequence[Any] = (), kwargs: Mapping[str, Any] | None = None,
                 margins: float | None = None) -> None:
        super().__init__(parent, Qt.WindowType.SplashScreen)

        self.setWindowModality(Qt.WindowModality.WindowModal)

        if isinstance(label, str):
            label = QLabel(label, self)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout: QGridLayout = QGridLayout(self)
        layout.addWidget(label)

        if margins is not None:
            layout.setContentsMargins(*([margins] * 4))

        self._target: Callable[[...], Any] = target
        self._args: Sequence[Any] = args
        self._kwargs: Mapping[str, Any] = kwargs or dict()
        self._thread: Thread | None = None

    @property
    def active(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def exec(self) -> None:
        self._thread = Thread(
            target=self._target,
            args=self._args,
            kwargs=self._kwargs)
        self.show()
        self._thread.start()
        while self.active:
            QCoreApplication.processEvents()
        self._thread.join()
        self._thread = None
        self.hide()

    def stop(self) -> None:
        if self._thread is not None:
            self._thread.join(0.0)
        self._thread = None
