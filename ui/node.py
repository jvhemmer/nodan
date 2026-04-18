from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ui.canvas import Canvas
    from core.node_system import CoreNode, CorePort

from PySide6.QtCore import Signal



from PySide6.QtGui import QBrush, QColor, QPen
from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsSimpleTextItem, QGraphicsItem, QMenu

from ui.port import UIPort
from ui.connection import UIConnection


class UINode(QGraphicsRectItem):
    # remove_requested = Signal(object) # QGraphicsObject

    def __init__(self, parent: Canvas, core_node: CoreNode, x=0, y=0, width=140, height=70, name="Node"):
        super().__init__(0, 0, width, height)
        self.view = parent
        self.core_node = core_node

        self.inputs = []
        self.outputs = []
        self._last_context_pos = None
        self.name = name

        self.setPos(x, y)

        self.setBrush(QBrush(QColor("#3b4252")))
        self.setPen(QPen(QColor("#88c0d0"), 2))

        self.setFlags(
            QGraphicsRectItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsRectItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsRectItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )

        self.label = QGraphicsSimpleTextItem(self)
        self.label.setBrush(QBrush(QColor("#eceff4")))
        self.label.setPos(12, 10)
        self.change_label(name)

    # TODO: Standardize how labeling is done in all classes
    def change_label(self, label: str):
        self.name = label
        self.label.setText(label)

    def delete(self):
        for port in self.get_all_ports():
            self.remove_port(port)

    def add_port(self, kind: str, core_port: CorePort) -> UIPort:
        port = UIPort(self, kind, core_port, 0, 0)
        if kind == "input":
            self.inputs.append(port)
        else:
            self.outputs.append(port)
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

        scene = self.scene()
        if scene is not None:
            scene.removeItem(port)

        self.layout_ports()

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

    def register_port(self, port: UIPort):
        port.clicked.connect(self.view.handle_port_click)

    def get_all_ports(self) -> list[UIPort]:
        ports = [p for p in self.inputs] + [p for p in self.outputs]
        return ports

    def contextMenuEvent(self, event):
        self._last_context_pos = event.pos()

        menu = QMenu()
        add_input_action = menu.addAction("Add input")
        add_output_action = menu.addAction("Add output")
        menu.addSeparator()
        delete_node = menu.addAction("Delete node")

        chosen = menu.exec(event.screenPos())

        if chosen == add_input_action:
            self.add_port("input")
        elif chosen == add_output_action:
            self.add_port("output")
        elif chosen == delete_node:
            # self.remove_requested.emit(self)
            # TODO: Change Node to QGraphicsItem to support signals and change this to a signal emition
            self.view.remove_node(self)
            pass

        event.accept()

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            for port in self.get_all_ports():
                for connection in port.connections:
                    connection.update_path()
        return super().itemChange(change, value)