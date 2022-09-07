# coding: utf-8

from contextlib import suppress

__all__ = ['QAbstractItemView', 'QAbstractSpinBox', 'QApplication', 'QCheckBox', 'QComboBox', 'QDialog',
           'QDialogButtonBox', 'QDoubleSpinBox', 'QFileDialog', 'QFormLayout', 'QGridLayout',
           'QGroupBox', 'QHBoxLayout', 'QHeaderView', 'QLabel', 'QLineEdit', 'QListWidget',
           'QListWidgetItem', 'QMainWindow', 'QMenu', 'QMenuBar', 'QMessageBox', 'QProgressBar',
           'QPushButton', 'QSpinBox', 'QStatusBar', 'QStyle', 'QStyleOptionViewItem',
           'QStyledItemDelegate', 'QTabWidget', 'QTableView', 'QTableWidgetSelectionRange',
           'QToolButton', 'QVBoxLayout', 'QWidget', 'QWizard', 'QWizardPage'
           ]

while True:
    with suppress(ImportError, ModuleNotFoundError):
        from PySide6.QtWidgets import (QAbstractItemView, QAbstractSpinBox, QApplication, QCheckBox, QComboBox, QDialog,
                                       QDialogButtonBox, QDoubleSpinBox, QFileDialog, QFormLayout, QGridLayout,
                                       QGroupBox, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QListWidget,
                                       QListWidgetItem, QMainWindow, QMenu, QMenuBar, QMessageBox, QProgressBar,
                                       QPushButton, QSpinBox, QStatusBar, QStyle, QStyleOptionViewItem,
                                       QStyledItemDelegate, QTabWidget, QTableView, QTableWidgetSelectionRange,
                                       QToolButton, QVBoxLayout, QWidget, QWizard, QWizardPage)
        break
    with suppress(ImportError, ModuleNotFoundError):
        from PyQt5.QtWidgets import (QAbstractItemView, QAbstractSpinBox, QApplication, QCheckBox, QComboBox, QDialog,
                                     QDialogButtonBox, QDoubleSpinBox, QFileDialog, QFormLayout, QGridLayout,
                                     QGroupBox, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QListWidget,
                                     QListWidgetItem, QMainWindow, QMenu, QMenuBar, QMessageBox, QProgressBar,
                                     QPushButton, QSpinBox, QStatusBar, QStyle, QStyleOptionViewItem,
                                     QStyledItemDelegate, QTabWidget, QTableView, QTableWidgetSelectionRange,
                                     QToolButton, QVBoxLayout, QWidget, QWizard, QWizardPage)
        break
    with suppress(ImportError, ModuleNotFoundError):
        from PyQt6.QtWidgets import (QAbstractItemView, QAbstractSpinBox, QApplication, QCheckBox, QComboBox, QDialog,
                                     QDialogButtonBox, QDoubleSpinBox, QFileDialog, QFormLayout, QGridLayout,
                                     QGroupBox, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QListWidget,
                                     QListWidgetItem, QMainWindow, QMenu, QMenuBar, QMessageBox, QProgressBar,
                                     QPushButton, QSpinBox, QStatusBar, QStyle, QStyleOptionViewItem,
                                     QStyledItemDelegate, QTabWidget, QTableView, QTableWidgetSelectionRange,
                                     QToolButton, QVBoxLayout, QWidget, QWizard, QWizardPage)
        break
    with suppress(ImportError, ModuleNotFoundError):
        from PySide2.QtWidgets import (QAbstractItemView, QAbstractSpinBox, QApplication, QCheckBox, QComboBox, QDialog,
                                       QDialogButtonBox, QDoubleSpinBox, QFileDialog, QFormLayout, QGridLayout,
                                       QGroupBox, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QListWidget,
                                       QListWidgetItem, QMainWindow, QMenu, QMenuBar, QMessageBox, QProgressBar,
                                       QPushButton, QSpinBox, QStatusBar, QStyle, QStyleOptionViewItem,
                                       QStyledItemDelegate, QTabWidget, QTableView, QTableWidgetSelectionRange,
                                       QToolButton, QVBoxLayout, QWidget, QWizard, QWizardPage)

        if not hasattr(QApplication, 'exec'):  # PySide2
            QApplication.exec = QApplication.exec_
        break
    raise ModuleNotFoundError('Cannot import QtWidgets from PySide6, PyQt5, PyQt6, or PySide2')
