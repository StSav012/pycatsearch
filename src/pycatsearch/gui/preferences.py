# -*- coding: utf-8 -*-
from __future__ import annotations

from functools import partial

from qtpy.QtWidgets import (QCheckBox, QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox, QFormLayout, QGroupBox,
                            QSpinBox, QVBoxLayout, QWidget)

from .settings import Settings

__all__ = ['Preferences']


class Preferences(QDialog):
    """ GUI preferences dialog """

    def __init__(self, settings: Settings, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.settings: Settings = settings
        self.setModal(True)
        self.setWindowTitle(self.tr('Preferences'))
        if parent is not None:
            self.setWindowIcon(parent.windowIcon())

        layout: QVBoxLayout = QVBoxLayout(self)
        check_box: QCheckBox
        combo_box: QComboBox
        spin_box: QSpinBox | QDoubleSpinBox
        for key, value in self.settings.DIALOG.items():
            if not (isinstance(value, dict) and value):
                continue
            box: QGroupBox = QGroupBox(key, self)
            box_layout: QFormLayout = QFormLayout(box)
            for key2, value2 in value.items():
                if isinstance(value2, tuple) and isinstance(value2[-1], str) and value2[-1]:
                    if len(value2) == 1:
                        check_box = QCheckBox(self.tr(key2), box)
                        setattr(check_box, 'callback', value2[-1])
                        check_box.setChecked(getattr(self.settings, value2[-1]))
                        check_box.toggled.connect(partial(self._on_event, sender=check_box))
                        box_layout.addWidget(check_box)
                    elif len(value2) == 2:
                        value3 = value2[0]
                        if isinstance(value3, (list, tuple)):
                            combo_box = QComboBox(box)
                            setattr(combo_box, 'callback', value2[-1])
                            for item in value3:
                                combo_box.addItem(self.tr(item))
                            combo_box.setCurrentIndex(getattr(self.settings, value2[-1]))
                            combo_box.currentIndexChanged.connect(
                                partial(self._on_combo_box_current_index_changed, sender=combo_box))
                            box_layout.addRow(self.tr(key2), combo_box)
                        # no else
                    elif len(value2) == 3:
                        value3a = value2[0]
                        value3b = value2[1]
                        if isinstance(value3a, (list, tuple)) and isinstance(value3b, (list, tuple)):
                            combo_box = QComboBox(box)
                            setattr(combo_box, 'callback', value2[-1])
                            for index, item in enumerate(value3a):
                                combo_box.addItem(self.tr(item), value3b[index])
                            combo_box.setCurrentIndex(value3b.index(getattr(self.settings, value2[-1])))
                            combo_box.currentIndexChanged.connect(
                                partial(self._on_combo_box_current_index_changed, sender=combo_box))
                            box_layout.addRow(self.tr(key2), combo_box)
                        elif (isinstance(value3a, slice)
                              and isinstance(getattr(self.settings, value2[-1]), (int, float))
                              and isinstance(value3b, tuple)):
                            if ((value3a.start is None or isinstance(value3a.start, int))
                                    and (value3a.stop is None or isinstance(value3a.stop, int))
                                    and (value3a.step is None or isinstance(value3a.step, int))
                                    and isinstance(getattr(self.settings, value2[-1]), int)):
                                spin_box = QSpinBox(box)
                            else:
                                spin_box = QDoubleSpinBox(box)
                            setattr(spin_box, 'callback', value2[-1])
                            if value3a.start is not None:
                                spin_box.setMinimum(value3a.start)
                            if value3a.stop is not None:
                                spin_box.setMaximum(value3a.stop)
                            if value3a.step is not None:
                                spin_box.setSingleStep(value3a.step)
                            spin_box.setValue(getattr(self.settings, value2[-1]))
                            if len(value3b) == 2:
                                spin_box.setPrefix(str(value3b[0]))
                                spin_box.setSuffix(str(value3b[1]))
                            elif len(value3b) == 1:
                                spin_box.setSuffix(str(value3b[0]))
                            # no else
                            spin_box.valueChanged.connect(partial(self._on_event, sender=spin_box))
                            box_layout.addRow(self.tr(key2), spin_box)
                        # no else
                    # no else
                # no else
                layout.addWidget(box)
        buttons: QDialogButtonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Close, self)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    # https://forum.qt.io/post/671245
    def _on_event(self, x: bool | int | float, sender: QWidget) -> None:
        setattr(self.settings, getattr(sender, 'callback'), x)

    def _on_combo_box_current_index_changed(self, _: int, sender: QComboBox) -> None:
        setattr(self.settings, getattr(sender, 'callback'), sender.currentData())
