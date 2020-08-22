# -*- coding: utf-8 -*-
from typing import Type

from PyQt5.QtWidgets import QCheckBox, QComboBox, \
    QDialog, QDialogButtonBox, QFormLayout, QGroupBox, \
    QVBoxLayout, QWidget

from settings import Settings

try:
    from typing import Final
except ImportError:
    class _Final:
        @staticmethod
        def __getitem__(item: Type):
            return item


    Final = _Final()


__all__ = ['Preferences']


class Preferences(QDialog):
    """ GUI preferences dialog """
    def __init__(self, settings: Settings, parent: QWidget = None, *args):
        super().__init__(parent, *args)

        self.settings: Settings = settings
        self.setModal(True)
        self.setWindowTitle(self.tr('Preferences'))
        if parent is not None:
            self.setWindowIcon(parent.windowIcon())

        layout: QVBoxLayout = QVBoxLayout(self)
        for key, value in self.settings.DIALOG.items():
            if isinstance(value, dict):
                box: QGroupBox = QGroupBox(key, self)
                box_layout: QFormLayout = QFormLayout(box)
                for key2, value2 in value.items():
                    if isinstance(value2, tuple):
                        if len(value2) == 1:
                            widget: QCheckBox = QCheckBox(self.tr(key2), box)
                            setattr(widget, 'callback', value2[-1])
                            widget.setChecked(getattr(self.settings, value2[-1]))
                            widget.toggled.connect(
                                lambda x: setattr(self.settings, getattr(self.sender(), 'callback'), x))
                            box_layout.addWidget(widget)
                        elif len(value2) == 2:
                            value3 = value2[0]
                            if isinstance(value3, (list, tuple)):
                                widget: QComboBox = QComboBox(box)
                                setattr(widget, 'callback', value2[-1])
                                for item in value3:
                                    widget.addItem(self.tr(item))
                                widget.setCurrentIndex(getattr(self.settings, value2[-1]))
                                widget.currentIndexChanged.connect(
                                    lambda x: setattr(self.settings, getattr(self.sender(), 'callback'), x))
                                box_layout.addRow(self.tr(key2), widget)
                            # no else
                        elif len(value2) == 3:
                            value3 = value2[0]
                            if isinstance(value3, (list, tuple)):
                                widget: QComboBox = QComboBox(box)
                                setattr(widget, 'callback', value2[-1])
                                for index, item in enumerate(value3):
                                    widget.addItem(self.tr(item), value2[1][index])
                                widget.setCurrentIndex(value2[1].index(getattr(self.settings, value2[-1])))
                                widget.currentIndexChanged.connect(
                                    lambda _: setattr(self.settings, getattr(self.sender(), 'callback'),
                                                      self.sender().currentData()))
                                box_layout.addRow(self.tr(key2), widget)
                            # no else
                        # no else
                    # no else
                layout.addWidget(box)
            # no else
        buttons: QDialogButtonBox = QDialogButtonBox(QDialogButtonBox.Close, self)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
