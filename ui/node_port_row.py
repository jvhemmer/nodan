from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd
from PySide6.QtGui import QBrush, QFont
from PySide6.QtWidgets import QGraphicsProxyWidget, QGraphicsSimpleTextItem, QLineEdit

if TYPE_CHECKING:
    from ui.node import UINode
    from ui.port import UIPort


class UINodePortRow:
    def __init__(self, node: UINode, port: UIPort):
        self.node = node
        self.port = port

        self.label_item = QGraphicsSimpleTextItem(port.name, node)
        self.label_item.setBrush(node._text_brush)
        font = self.label_item.font()
        font.setFamily("Ubuntu Mono")
        self.label_item.setFont(font)

        self.proxy = QGraphicsProxyWidget(node)
        self.line_edit = QLineEdit()
        self.line_edit.setFont(QFont("Ubuntu Mono", 9))
        self.proxy.setWidget(self.line_edit)

        if port.kind == "input":
            self.line_edit.setPlaceholderText("value")
            self.line_edit.editingFinished.connect(self._on_edit_finished)
        else:
            self.line_edit.setReadOnly(True)

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
        label_y = row_center_y - (self.label_item.boundingRect().height() / 2)
        self.label_item.setPos(label_x, label_y)
        self.proxy.setPos(field_x, row_center_y - (field_height / 2))
        self.line_edit.setFixedWidth(int(field_width))
        self.line_edit.setFixedHeight(field_height)

    def label_width(self) -> float:
        return self.label_item.boundingRect().width()

    def field_width_hint(self) -> float:
        return self.line_edit.sizeHint().width()

    def _on_edit_finished(self) -> None:
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
