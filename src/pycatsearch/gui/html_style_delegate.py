# -*- coding: utf-8 -*-
from __future__ import annotations

from qtpy.QtCore import QModelIndex, QPersistentModelIndex, QRect, QSize
from qtpy.QtGui import QAbstractTextDocumentLayout, QPainter, QTextDocument
from qtpy.QtWidgets import QApplication, QStyle, QStyleOptionViewItem, QStyledItemDelegate

__all__ = ["HTMLDelegate"]


class HTMLDelegate(QStyledItemDelegate):
    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionViewItem,
        index: QModelIndex | QPersistentModelIndex,
    ) -> None:
        self.initStyleOption(option, index)
        style: QStyle
        if option.widget:
            style = option.widget.style()
        else:
            style = QApplication.style()
        doc: QTextDocument = QTextDocument()
        doc.setHtml(option.text)
        option.text = ""
        style.drawControl(QStyle.ControlElement.CE_ItemViewItem, option, painter)
        ctx: QAbstractTextDocumentLayout.PaintContext = QAbstractTextDocumentLayout.PaintContext()
        text_rect: QRect = style.subElementRect(QStyle.SubElement.SE_ItemViewItemText, option)
        painter.save()
        painter.translate(text_rect.topLeft())
        painter.setClipRect(option.rect.translated(-text_rect.topLeft()))
        painter.translate(0, 0.5 * (option.rect.height() - doc.size().height()))
        doc.documentLayout().draw(painter, ctx)
        painter.restore()

    def sizeHint(self, option: QStyleOptionViewItem | None, index: QModelIndex | QPersistentModelIndex) -> QSize:
        options: QStyleOptionViewItem = QStyleOptionViewItem(option)
        self.initStyleOption(options, index)
        doc: QTextDocument = QTextDocument()
        doc.setHtml(options.text)
        doc.setTextWidth(options.rect.width())
        return QSize(round(doc.idealWidth()), round(QTextDocument().size().height()))
