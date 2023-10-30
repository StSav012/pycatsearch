# -*- coding: utf-8 -*-
from __future__ import annotations

from threading import Thread
from typing import Any, Callable, Mapping, Sequence

from qtpy.QtCore import QCoreApplication, QSize, Qt
from qtpy.QtWidgets import QLabel, QVBoxLayout, QWidget

__all__ = ["WaitingScreen"]


def _spinner(parent: QWidget | None = None) -> QWidget | None:
    from contextlib import suppress

    with suppress(ImportError, Exception):
        import qtawesome as qta

        spinner: qta.IconWidget = qta.IconWidget(parent=parent)
        spinner.setIconSize(QSize(*([spinner.fontMetrics().height() * 2] * 2)))
        # might raise an `Exception` if the icon is not in the font
        spinner.setIcon(qta.icon("mdi6.loading", animation=qta.Spin(spinner, interval=16, step=4)))
        spinner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return spinner

    return None


class WaitingScreen(QWidget):
    def __init__(
        self,
        parent: QWidget,
        label: str | QWidget,
        target: Callable[[...], Any],
        args: Sequence[Any] = (),
        kwargs: Mapping[str, Any] | None = None,
        margins: float | None = None,
    ) -> None:
        super().__init__(parent, Qt.WindowType.SplashScreen)

        self.setWindowModality(Qt.WindowModality.WindowModal)

        if isinstance(label, str):
            label = QLabel(label, self)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout: QVBoxLayout = QVBoxLayout(self)
        spinner: QWidget | None = _spinner(self)
        if spinner is not None:
            layout.addWidget(spinner)
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
        self._thread = Thread(target=self._target, args=self._args, kwargs=self._kwargs)
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


if __name__ == "__main__":
    import sys

    from qtpy.QtWidgets import QApplication

    app: QApplication = QApplication(sys.argv)
    w: WaitingScreen = WaitingScreen(None, "label", None)  # type: ignore
    w.hideEvent = lambda event: app.quit()
    w.show()
    app.exec()
