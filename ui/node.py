from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ui.canvas import Canvas

from PySide6.QtCore import QPointF, QPoint
from PySide6.QtGui import QBrush, QColor, QPen, QPainterPath, QAction
from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsSimpleTextItem, QGraphicsPathItem, QGraphicsEllipseItem, \
    QGraphicsItem, QWidget, QMenu

import math

from ui.port import Port
from ui.connection import Connection

class Node(QGraphicsRectItem):
    def __init__(self, parent: Canvas, x=0, y=0, width=140, height=70, title="Node"):
        super().__init__(0, 0, width, height)
        self.view = parent
        self.inputs = []
        self.outputs = []
        self._last_context_pos = None

        self.setPos(x, y)

        self.setBrush(QBrush(QColor("#3b4252")))
        self.setPen(QPen(QColor("#88c0d0"), 2))

        self.setFlags(
            QGraphicsRectItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsRectItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsRectItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )

        self.label = QGraphicsSimpleTextItem(title, self)
        self.label.setBrush(QBrush(QColor("#eceff4")))
        self.label.setPos(12, 10)

        # self.input = Port(self, "input", x=width/2, y=0)
        # self.output = Port(self, "output", x=width/2, y=height)

        self.input = self.add_port("input")
        self.output = self.add_port("output")

    def add_port(self, kind: str) -> Port:
        port = Port(self, kind, 0, 0)
        if kind == "input":
            self.inputs.append(port)
        else:
            self.outputs.append(port)
        self.register_port(port)
        self.layout_ports()
        return port

    def layout_ports(self):
        rect = self.rect()
        self._layout_port_group(self.inputs, rect.top())
        self._layout_port_group(self.outputs, rect.bottom())

    def _layout_port_group(self, ports, y):
        if not ports:
            return

        rect = self.rect()
        step = rect.width() / (len(ports) + 1)
        for i, port in enumerate(ports):
            port.setPos(step * (i + 1), y)
            port.refresh_connections()

    def register_port(self, port: Port):
        port.clicked.connect(self.view.handle_port_click)

    def get_all_ports(self) -> list[Port]:
        ports = [p for p in self.inputs] + [p for p in self.outputs]
        return ports

    def contextMenuEvent(self, event):
        self._last_context_pos = event.pos()

        menu = QMenu()
        add_input_action = menu.addAction("Add input")
        add_output_action = menu.addAction("Add output")

        chosen = menu.exec(event.screenPos())

        if chosen == add_input_action:
            self.add_port("input")
        elif chosen == add_output_action:
            self.add_port("output")

        event.accept()

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            for port in self.get_all_ports():
                for connection in port.connections:
                    connection.update_path()
        return super().itemChange(change, value)