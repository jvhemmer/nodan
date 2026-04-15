from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ui.node import Node
    from ui.connection import Connection

from PySide6.QtCore import QPointF, QPoint, Signal, QRectF
from PySide6.QtGui import QBrush, QColor, QPen, QPainterPath
from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsSimpleTextItem, QGraphicsPathItem, QGraphicsEllipseItem, \
    QGraphicsItem, QGraphicsObject

import numpy as np

class Port(QGraphicsObject):
    clicked = Signal(object)

    def __init__(self, parent: Node, kind: str, x: float, y: float, radius=6):
        super().__init__(parent)
        self.hit_radius = 5
        self.node = parent
        self.kind = kind
        self.radius = radius
        self.connections = []
        self.hovered = False
        self.setPos(x, y)

        self.setAcceptHoverEvents(True)

    def calculate_hit_radius(self) -> float:
        return self.radius + 5 + 2*len(self.connections)

    def boundingRect(self):
        r = self.calculate_hit_radius()
        return QRectF(-r, -r, r * 2, r * 2)

    def shape(self):
        path = QPainterPath()
        r = self.calculate_hit_radius() if self.hovered else self.radius
        path.addEllipse(-r, -r, r * 2, r * 2)
        return path

    def paint(self, painter, option, widget=None):
        painter.setBrush(QBrush(QColor("#d08770") if self.kind == "input" else QColor("#a3be8c")))
        painter.setPen(QPen(QColor("#2e3440"), 2))

        r = self.radius
        painter.drawEllipse(-r, -r, r * 2, r * 2)

    def scene_center(self):
        """Returns the center of the Port in Scene coordinates."""
        return self.mapToScene(self.boundingRect().center())

    def add_connection(self, connection: Connection):
        if connection not in self.connections:
            self.connections.append(connection)

    def refresh_connections(self):
        for connection in self.connections:
            connection.update_path()

    def connection_anchor(self, connection: Connection):
        """Calculates where the connection should connect to."""
        center = self.scene_center()

        if not self.hovered or connection not in self.connections:
            return center

        # If Port is being hovered:
        if self.kind == "input":
            sign = -1
        else:
            sign = 1

        ordered = sorted(
            self.connections,
            key=lambda c: self.other_node_pos(c).x()
        )
        ordered = ordered[::-sign] # flip order if output
        index = ordered.index(connection)
        count = len(ordered)

        radius = 15 + ((count-1) * 1)

        base_angle = sign * np.pi / 2 # up or down

        if count == 1:
            angle = base_angle
        else:
            max_spread = np.radians(120)

            used_spread: float = min(max_spread, np.radians(60 * (count - 1)))

            start = base_angle - used_spread / 2
            step = used_spread / (count - 1)
            angle = start + index * step

        return QPointF(
            center.x() + radius * np.cos(angle),
            center.y() + radius * np.sin(angle),
        )

    def is_connected_to(self, target: Port) -> bool:
        for connection in self.connections:
            if connection.target is target:
                return True
        return False

    def other_node_pos(self, connection: Connection):
        if connection.source is self and connection.target is not None:
            return connection.target.node.sceneBoundingRect().center()

        if connection.target is self:
            return connection.source.node.sceneBoundingRect().center()

        return self.scene_center()

    def mousePressEvent(self, event):
        self.clicked.emit(self)
        event.accept()

    def hoverEnterEvent(self, event):
        self.prepareGeometryChange()
        self.hovered = True
        self.setScale(1.25)
        self.refresh_connections()
        self.update()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.prepareGeometryChange()
        self.hovered = False
        self.setScale(1.0)
        self.refresh_connections()
        self.update()
        super().hoverLeaveEvent(event)