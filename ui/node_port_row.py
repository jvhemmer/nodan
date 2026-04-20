from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd
from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QGraphicsProxyWidget, QGraphicsSimpleTextItem, QLineEdit

if TYPE_CHECKING:
    from ui.node import UINode
    from ui.port import UIPort


class PortValueLineEdit(QLineEdit):
    submitted = Signal()
    hover_entered = Signal()
    hover_left = Signal()

    def keyPressEvent(self, event) -> None:
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.submitted.emit()
            event.accept()
            return
        super().keyPressEvent(event)

    def enterEvent(self, event) -> None:
        self.hover_entered.emit()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self.hover_left.emit()
        super().leaveEvent(event)


class UINodePortRow:
    def __init__(self, node: UINode, port: UIPort):
        self.node = node
        self.port = port

        self._submitted_by_return = False
        self._base_field_width = 0
        self._field_height = 0

        self.label_item = QGraphicsSimpleTextItem(port.name, node)
        self.label_item.setBrush(node._text_brush)
        font = self.label_item.font()
        font.setFamily("Space Mono")
        font.setBold(True)
        font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
        font.setHintingPreference(QFont.HintingPreference.PreferNoHinting)
        self.label_item.setFont(font)

        self.proxy = QGraphicsProxyWidget(node)
        self.line_edit = self._build_line_edit()
        self.proxy.setWidget(self.line_edit)

    def delete(self) -> None:
        scene = self.node.scene()
        if scene is None:
            return
        scene.removeItem(self.label_item)
        scene.removeItem(self.proxy)

    def sync(self) -> None:
        self.label_item.setText(self.port.name)
        text = self._format_value(self.port.core_port.value)
        if self.line_edit.text() != text:
            self.line_edit.setText(text)
        if self.port.kind == "input":
            self.line_edit.setReadOnly(not (self.port.is_editable() and not self.port.has_connection()))

    def set_geometry(self, label_x: float, row_center_y: float, field_x: float, field_width: float, field_height: int) -> None:
        self._base_field_width = int(field_width)
        self._field_height = field_height
        label_y = row_center_y - (self.label_item.boundingRect().height() / 2)
        self.label_item.setPos(label_x, label_y)
        self.proxy.setPos(field_x, row_center_y - (field_height / 2))
        self.line_edit.setFixedWidth(self._base_field_width)
        self.line_edit.setFixedHeight(field_height)

    def label_width(self) -> float:
        return self.label_item.boundingRect().width()

    def field_width_hint(self) -> float:
        return self.line_edit.sizeHint().width()

    def _on_edit_finished(self) -> None:
        if self._submitted_by_return:
            self._submitted_by_return = False
            return

        if not self.port.is_editable() or self.port.has_connection():
            self.sync()
            return

        self.node.view.coordinator.set_port_value(self.port, self.line_edit.text())
        self.line_edit.clearFocus()
        self.sync()

    def _format_value(self, value) -> str:
        if value is None:
            return ""
        if isinstance(value, pd.DataFrame):
            rows, cols = value.shape
            return f"{rows}x{cols} DataFrame"
        return str(value)

    def _on_return_pressed(self) -> None:
        self._submitted_by_return = True
        if not self.port.is_editable() or self.port.has_connection():
            self.sync()
        else:
            self.node.view.coordinator.set_port_value(self.port, self.line_edit.text())
            self.sync()

        self.line_edit.clearFocus()
        self._rebuild_editor()
        QTimer.singleShot(0, self.node.view.viewport().setFocus)

    def _build_line_edit(self) -> PortValueLineEdit:
        line_edit = PortValueLineEdit()
        font = QFont("Space Mono", 9)
        font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
        font.setHintingPreference(QFont.HintingPreference.PreferNoHinting)
        line_edit.setFont(font)
        line_edit.hover_entered.connect(self._expand_if_needed)
        line_edit.hover_left.connect(self._restore_width)

        if self.port.kind == "input":
            line_edit.setPlaceholderText("value")
            line_edit.editingFinished.connect(self._on_edit_finished)
            line_edit.submitted.connect(self._on_return_pressed)
        else:
            line_edit.setReadOnly(True)

        return line_edit

    def _rebuild_editor(self) -> None:
        old_widget = self.line_edit
        width = old_widget.width()
        height = old_widget.height()
        proxy_pos = self.proxy.pos()
        self.line_edit = self._build_line_edit()
        self.proxy.setWidget(self.line_edit)
        self.proxy.setPos(proxy_pos)
        if width > 0:
            self.line_edit.setFixedWidth(width)
        if height > 0:
            self.line_edit.setFixedHeight(height)
        self.sync()

    def _expand_if_needed(self) -> None:
        if self._base_field_width <= 0:
            return

        text = self.line_edit.text() or self.line_edit.placeholderText()
        text_width = self.line_edit.fontMetrics().horizontalAdvance(text)
        target_width = text_width + 18
        if target_width > self._base_field_width:
            self.line_edit.setFixedWidth(target_width)
        self.node.setZValue(1000)

    def _restore_width(self) -> None:
        if self._base_field_width > 0:
            self.line_edit.setFixedWidth(self._base_field_width)
        self.node.setZValue(1)
