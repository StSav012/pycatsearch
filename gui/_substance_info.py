# -*- coding: utf-8 -*-
from typing import Any, Optional

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QFormLayout, QLabel, QWidget

from catalog import Catalog
from utils import *

__all__ = ['SubstanceInfo']


class SubstanceInfo(QDialog):
    """ simple dialog that displays the information about a substance from the loaded catalog """
    def __init__(self, catalog: Catalog, entry_id: int, parent: Optional[QWidget] = None, *args: Any) -> None:
        super().__init__(parent, *args)
        self.setModal(True)
        self.setWindowTitle(self.tr('Substance Info'))
        if parent is not None:
            self.setWindowIcon(parent.windowIcon())
        layout: QFormLayout = QFormLayout(self)
        label: QLabel
        for entry in catalog.catalog:
            if entry[ID] == entry_id:
                for key in entry:
                    if key == LINES:
                        continue
                    elif key == STATE_HTML:
                        label = QLabel(chem_html(str(entry[key])), self)
                    elif key == INCHI_KEY:
                        label = \
                            QLabel(f'<a href="https://pubchem.ncbi.nlm.nih.gov/#query={entry[key]}">{entry[key]}</a>',
                                   self)
                        label.setOpenExternalLinks(True)
                    else:
                        label = QLabel(str(entry[key]), self)
                    label.setTextInteractionFlags(Qt.TextBrowserInteraction)
                    layout.addRow(self.tr(HUMAN_READABLE[key]), label)
        buttons: QDialogButtonBox = QDialogButtonBox(QDialogButtonBox.Close, self)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
