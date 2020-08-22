# -*- coding: utf-8 -*-
from typing import Type

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QFormLayout, QLabel, QWidget

from catalog import Catalog
from utils import *

try:
    from typing import Final
except ImportError:
    class _Final:
        @staticmethod
        def __getitem__(item: Type):
            return item


    Final = _Final()


__all__ = ['SubstanceInfo']


class SubstanceInfo(QDialog):
    """ simple dialog that displays the information about a substance from the loaded catalog """
    def __init__(self, catalog: Catalog, entry_id: int, parent: QWidget = None, *args):
        super().__init__(parent, *args)
        self.setModal(True)
        self.setWindowTitle(self.tr('Substance Info'))
        if parent is not None:
            self.setWindowIcon(parent.windowIcon())
        layout: QFormLayout = QFormLayout(self)
        for entry in catalog.catalog:
            if entry[ID] == entry_id:
                for key in entry:
                    if key == LINES:
                        continue
                    elif key == STATE_HTML:
                        label: QLabel = QLabel(chem_html(entry[key]), self)
                        label.setTextInteractionFlags(Qt.TextBrowserInteraction)
                        layout.addRow(self.tr(HUMAN_READABLE[key]), label)
                    elif key == INCHI_KEY:
                        label: QLabel = \
                            QLabel(f'<a href="https://pubchem.ncbi.nlm.nih.gov/#query={entry[key]}">{entry[key]}</a>',
                                   self)
                        label.setTextInteractionFlags(Qt.TextBrowserInteraction)
                        label.setOpenExternalLinks(True)
                        layout.addRow(self.tr(HUMAN_READABLE[key]), label)
                    else:
                        label: QLabel = QLabel(str(entry[key]), self)
                        label.setTextInteractionFlags(Qt.TextBrowserInteraction)
                        layout.addRow(self.tr(HUMAN_READABLE[key]), label)
        buttons: QDialogButtonBox = QDialogButtonBox(QDialogButtonBox.Close, self)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
