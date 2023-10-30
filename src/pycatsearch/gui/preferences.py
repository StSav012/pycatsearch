# -*- coding: utf-8 -*-
from __future__ import annotations

import logging
from functools import partial
from typing import Any, Hashable, cast

from qtpy.QtCore import QByteArray, Qt
from qtpy.QtGui import QCloseEvent
from qtpy.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QScrollArea,
    QSpinBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from .settings import Settings

__all__ = ["Preferences"]


class PreferencePage(QWidget):
    """A page of the Preferences dialog"""

    def __init__(
        self,
        value: dict[
            str,
            (
                Settings.CallbackOnly
                | Settings.SpinboxAndCallback
                | Settings.ComboboxAndCallback
                | Settings.EditableComboboxAndCallback
            ),
        ],
        settings: Settings,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.settings: Settings = settings
        logger: logging.Logger = logging.getLogger("preferences")

        if not (isinstance(value, dict) and value):
            raise TypeError(f"Invalid type: {type(value)}")
        layout: QFormLayout = QFormLayout(self)
        key2: str
        value2: (
            Settings.CallbackOnly
            | Settings.SpinboxAndCallback
            | Settings.ComboboxAndCallback
            | Settings.EditableComboboxAndCallback
        )

        check_box: QCheckBox
        spin_box: QSpinBox | QDoubleSpinBox
        combo_box: QComboBox

        for key2, value2 in value.items():
            if isinstance(value2, Settings.CallbackOnly):
                if isinstance(getattr(self.settings, value2.callback), bool):
                    check_box = QCheckBox(self.settings.tr(key2), self)
                    setattr(check_box, "callback", value2.callback)
                    check_box.setChecked(getattr(self.settings, value2.callback))
                    check_box.toggled.connect(partial(self._on_event, sender=check_box))
                    layout.addWidget(check_box)
                else:
                    logger.error(f"The type of {value2.callback!r} is not supported")
            elif isinstance(value2, Settings.SpinboxAndCallback):
                if isinstance(getattr(self.settings, value2.callback), int):
                    spin_box = QSpinBox(self)
                else:
                    spin_box = QDoubleSpinBox(self)
                spin_box.setValue(getattr(self.settings, value2.callback))
                spin_box.setRange(value2.range.start, value2.range.stop)
                spin_box.setSingleStep(value2.range.step or 1)
                spin_box.setPrefix(value2.prefix_and_suffix[0])
                spin_box.setSuffix(value2.prefix_and_suffix[1])
                setattr(spin_box, "callback", value2.callback)
                spin_box.valueChanged.connect(partial(self._on_event, sender=spin_box))
                layout.addRow(key2, spin_box)
            elif isinstance(value2, Settings.ComboboxAndCallback):
                combo_box = QComboBox(self)
                setattr(combo_box, "callback", value2.callback)
                combobox_data: dict[Hashable, str]
                if isinstance(value2.combobox_data, dict):
                    combobox_data = value2.combobox_data
                else:
                    combobox_data = dict(enumerate(value2.combobox_data))
                for index, (data, item) in enumerate(combobox_data.items()):
                    combo_box.addItem(self.settings.tr(item), data)
                combo_box.setEditable(False)
                combo_box.setCurrentText(combobox_data[getattr(self.settings, value2.callback)])
                combo_box.currentIndexChanged.connect(
                    partial(self._on_combo_box_current_index_changed, sender=combo_box)
                )
                layout.addRow(self.settings.tr(key2), combo_box)
            elif isinstance(value2, Settings.EditableComboboxAndCallback):
                combo_box = QComboBox(self)
                setattr(combo_box, "callback", value2.callback)
                combo_box.addItems(value2.combobox_items)
                current_text: str = getattr(self.settings, value2.callback)
                if current_text in value2.combobox_items:
                    combo_box.setCurrentIndex(value2.combobox_items.index(current_text))
                else:
                    combo_box.insertItem(0, current_text)
                    combo_box.setCurrentIndex(0)
                combo_box.setEditable(True)
                combo_box.currentTextChanged.connect(partial(self._on_event, sender=combo_box))
                layout.addRow(self.settings.tr(key2), combo_box)
            else:
                logger.error(f"{value2!r} is not supported")

    # https://forum.qt.io/post/671245
    def _on_event(self, x: bool | int | float | str, sender: QWidget) -> None:
        setattr(self.settings, getattr(sender, "callback"), x)

    def _on_combo_box_current_index_changed(self, _: int, sender: QComboBox) -> None:
        setattr(self.settings, getattr(sender, "callback"), sender.currentData())


class PreferencesBody(QScrollArea):
    """The main area of the GUI preferences dialog"""

    def __init__(self, settings: Settings, parent: QWidget | None = None) -> None:
        from . import qta_icon  # import locally to avoid a circular import

        super().__init__(parent)

        self.settings: Settings = settings
        logger: logging.Logger = logging.getLogger("preferences")

        widget: QWidget = QWidget(self)
        self.setWidget(widget)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setFrameStyle(0)

        layout: QHBoxLayout = QHBoxLayout(widget)
        content: QListWidget = QListWidget(widget)
        stack: QStackedWidget = QStackedWidget(widget)
        key: str | tuple[str, tuple[str, ...]] | tuple[str, tuple[str, ...], tuple[tuple[str, Any], ...]]
        value: dict[
            str,
            (
                Settings.CallbackOnly
                | Settings.SpinboxAndCallback
                | Settings.ComboboxAndCallback
                | Settings.EditableComboboxAndCallback
            ),
        ]
        for key, value in self.settings.dialog.items():
            if not (isinstance(value, dict) and value):
                logger.error(f"Invalid value of {key!r}")
                continue
            new_item: QListWidgetItem
            if isinstance(key, str):
                new_item = QListWidgetItem(key)
            elif isinstance(key, tuple):
                if len(key) == 1:
                    new_item = QListWidgetItem(key[0])
                elif len(key) == 2:
                    new_item = QListWidgetItem(qta_icon(*key[1]), key[0])
                elif len(key) == 3:
                    new_item = QListWidgetItem(qta_icon(*key[1], **dict(key[2])), key[0])
                else:
                    logger.error(f"Invalid key: {key!r}")
                    continue
            else:
                logger.error(f"Invalid key type: {key!r}")
                continue
            content.addItem(new_item)
            box: PreferencePage = PreferencePage(value, settings, self)
            stack.addWidget(box)
        content.setMinimumWidth(content.sizeHintForColumn(0) + 2 * content.frameWidth())
        layout.addWidget(content)
        layout.addWidget(stack)

        if content.count() > 0:
            content.setCurrentRow(0)  # select the first page

        content.currentRowChanged.connect(stack.setCurrentIndex)


class Preferences(QDialog):
    """GUI preferences dialog"""

    def __init__(self, settings: Settings, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.settings: Settings = settings
        self.setModal(True)
        self.setWindowTitle(self.tr("Preferences"))
        if parent is not None:
            self.setWindowIcon(parent.windowIcon())

        layout: QVBoxLayout = QVBoxLayout(self)
        layout.addWidget(PreferencesBody(settings=settings, parent=parent))
        buttons: QDialogButtonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Close, self)
        buttons.rejected.connect(self.close)
        layout.addWidget(buttons)

        self.settings.beginGroup("PreferencesDialog")
        self.restoreGeometry(cast(QByteArray, self.settings.value("windowGeometry", QByteArray())))
        self.settings.endGroup()

    def closeEvent(self, event: QCloseEvent) -> None:
        self.settings.beginGroup("PreferencesDialog")
        self.settings.setValue("windowGeometry", self.saveGeometry())
        self.settings.endGroup()
