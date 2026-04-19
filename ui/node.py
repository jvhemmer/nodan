from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor, QFont, QPen
from PySide6.QtWidgets import QGraphicsItem, QGraphicsRectItem, QGraphicsSimpleTextItem, QMenu

from ui.node_port_row import UINodePortRow
from ui.port import UIPort

if TYPE_CHECKING:
    from core.node_system import CoreNode, CorePort
    from ui.canvas import Canvas


class UINode(QGraphicsRectItem):
    def __init__(self, parent: Canvas, core_node: CoreNode, x=0, y=0, width=380, height=140, name="Node"):
        super().__init__(0, 0, width, height)
        self.view = parent
        self.core_node = core_node

        self.inputs: list[UIPort] = []
        self.outputs: list[UIPort] = []
        self._input_rows: dict[UIPort, UINodePortRow] = {}
        self._output_rows: dict[UIPort, UINodePortRow] = {}
        self._last_context_pos = None
        self.name = name

        self._corner_radius = 8
        self._content_margin = 16
        self._title_height = 26
        self._body_top_gap = 6
        self._row_height = 24
        self._horizontal_gap = 12
        self._field_height = 20
        self._min_label_width = 60
        self._field_width = 100

        self._header_brush = QBrush(QColor("#2a2a2a"))
        self._text_brush = QBrush(QColor("#eceff4"))
        self._fill_brush = QBrush(QColor("#1e1e1e"))
        self._edge_pen = QPen(QColor("#262626"), 2)

        self.setPos(x, y)

        self.setBrush(self._fill_brush)
        self.setPen(self._edge_pen)

        self.setFlags(
            QGraphicsRectItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsRectItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsRectItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )

        self.title = QGraphicsSimpleTextItem(self)
        self.title.setBrush(self._text_brush)
        self.change_label(name)

    def paint(self, painter, option, widget=None):
        painter.setBrush(self.brush())
        painter.setPen(self.pen())
        painter.drawRoundedRect(self.rect(), self._corner_radius, self._corner_radius)

        painter.setBrush(self._header_brush)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(0, 0, self.rect().width(), self._title_height, self._corner_radius, self._corner_radius)
        painter.drawRect(0, self._title_height / 2, self.rect().width(), self._title_height / 2)

    def change_label(self, label: str):
        self.name = label
        self.title.setText(label)
        font = QFont("Ubuntu", 10)
        font.setBold(True)
        self.title.setFont(font)
        self._layout_title()

    def delete(self):
        for port in self.get_all_ports():
            self.remove_port(port)

    def add_port(self, kind: str, core_port: CorePort) -> UIPort:
        port = UIPort(self, kind, core_port, 0, 0, name=core_port.spec.name)
        if kind == "input":
            self.inputs.append(port)
            self._input_rows[port] = UINodePortRow(self, port)
        else:
            self.outputs.append(port)
            self._output_rows[port] = UINodePortRow(self, port)
        self.register_port(port)
        self.layout_ports()
        return port

    def remove_port(self, port: UIPort):
        ports = self.inputs if port.kind == "input" else self.outputs
        if port not in ports:
            return

        for connection in port.connections.copy():
            connection.delete()

        ports.remove(port)

        rows = self._input_rows if port.kind == "input" else self._output_rows
        row = rows.pop(port)
        scene = self.scene()
        if scene is not None:
            row.delete()
            scene.removeItem(port)

        self.layout_ports()

    def sync_port_widgets(self) -> None:
        for row in self._input_rows.values():
            row.sync()
        for row in self._output_rows.values():
            row.sync()

    def layout_ports(self):
        rows = max(len(self.inputs) + len(self.outputs), 1)
        label_width = self._compute_label_width()
        field_width = self._compute_field_width()
        content_width = (
            self._content_margin
            + label_width
            + self._horizontal_gap
            + field_width
            + self._content_margin
        )
        title_width = self.title.boundingRect().width() + (self._content_margin * 2)
        width = max(content_width, title_width)
        height = self._title_height + self._body_top_gap + (rows * self._row_height) + self._content_margin / 2
        self.setRect(0, 0, width, height)

        self._layout_title()
        self._layout_inputs(label_width, field_width)
        self._layout_outputs(label_width, field_width)
        self.sync_port_widgets()

    def _layout_inputs(self, label_width: float, field_width: float) -> None:
        for index, port in enumerate(self.inputs):
            row_center_y = self._title_height + self._body_top_gap + (index * self._row_height) + (self._row_height / 2)
            port.setPos(0, row_center_y)
            self._input_rows[port].set_geometry(
                self._content_margin,
                row_center_y,
                self._content_margin + label_width + self._horizontal_gap,
                field_width,
                self._field_height,
            )
            port.refresh_connections()

    def _layout_outputs(self, label_width: float, field_width: float) -> None:
        right_edge = self.rect().width()
        label_x = self._content_margin
        value_x = self._content_margin + label_width + self._horizontal_gap

        for index, port in enumerate(self.outputs):
            row_index = len(self.inputs) + index
            row_center_y = self._title_height + self._body_top_gap + (row_index * self._row_height) + (self._row_height / 2)
            port.setPos(right_edge, row_center_y)
            self._output_rows[port].set_geometry(
                label_x,
                row_center_y,
                value_x,
                field_width,
                self._field_height,
            )
            port.refresh_connections()

    def _compute_label_width(self) -> float:
        labels = [self._min_label_width]
        for row in self._input_rows.values():
            labels.append(row.label_width())
        for row in self._output_rows.values():
            labels.append(row.label_width())
        return max(labels)

    def _compute_field_width(self) -> float:
        widths = [self._field_width]
        for row in self._input_rows.values():
            widths.append(row.field_width_hint())
        for row in self._output_rows.values():
            widths.append(row.field_width_hint())
        return max(widths)

    def _layout_title(self) -> None:
        title_rect = self.title.boundingRect()
        title_y = (self._title_height - title_rect.height()) / 2
        self.title.setPos(self._content_margin, title_y)

    def register_port(self, port: UIPort):
        port.clicked.connect(self.view.handle_port_click)

    def get_all_ports(self) -> list[UIPort]:
        return [*self.inputs, *self.outputs]

    def contextMenuEvent(self, event):
        self._last_context_pos = event.pos()

        menu = QMenu()
        delete_node = menu.addAction("Delete node")

        chosen = menu.exec(event.screenPos())

        if chosen == delete_node:
            self.view.remove_node(self)

        event.accept()

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            for port in self.get_all_ports():
                for connection in port.connections:
                    connection.update_path()
        return super().itemChange(change, value)
