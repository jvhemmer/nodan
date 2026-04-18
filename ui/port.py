from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ui.node import UINode
    from ui.connection import UIConnection

from PySide6.QtCore import QPointF, Signal, QRectF, QLineF, QEvent, QPoint
from PySide6.QtGui import QBrush, QColor, QPen, QCursor, QMouseEvent, QPainter, QFont
from PySide6.QtWidgets import QGraphicsObject

from core.node_system import PortSpec, CorePort

import numpy as np


class UIPort(QGraphicsObject):
    clicked = Signal(object)
    moved_away = Signal(object)

    def __init__(self, parent: UINode, kind: str, core_port: CorePort, x: float, y: float, name: str = "New port", radius=6):
        super().__init__(parent)
        self.ui_node: UINode = parent # to satisfy annoying checker
        self.kind = kind
        self.core_port = core_port
        self.radius = radius
        self.name = name

        self.text_painter = QPainter()

        self.connections = []

        self.hovered = False
        self.threshold = 25
        self._tracking = False
        self._outside = False
        self.show_name = False

        self.setPos(x, y)

        self.setZValue(1)

        self.setAcceptHoverEvents(True)

    def boundingRect(self):
        r = self.radius
        return QRectF(-r, -r, r * 2, r * 2)

    def draw_name(self, painter):
        painter.setPen(QColor("#eceff4"))
        painter.setFont(QFont("Segoe UI", 7))
        if self.kind == "input":
            text_pos = QPointF(7.5, -7.5)
        else:
            text_pos = QPointF(7.5, self.boundingRect().height() / 2 + 7.5)
        painter.drawText(text_pos, self.name)

    def paint(self, painter, option, widget=None):
        painter.setBrush(QBrush(QColor("#d08770") if self.kind == "input" else QColor("#a3be8c")))
        painter.setPen(QPen(QColor("#2e3440"), 2))
        painter.drawEllipse(self.boundingRect())
        if self.hovered or self.show_name:
            self.draw_name(painter)

    def scene_center(self):
        """Returns the center of the Port in Scene coordinates."""
        return self.mapToScene(self.boundingRect().center())

    def add_connection(self, connection: UIConnection):
        if connection not in self.connections:
            self.connections.append(connection)

    def refresh_connections(self):
        for connection in self.connections:
            connection.update_path()

    def connection_anchor(self, connection: UIConnection):
        """Calculates where the connection should connect to."""
        center = self.scene_center()

        if (not self.hovered and self._outside) or connection not in self.connections:
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

    def is_connected_to(self, target: UIPort) -> bool:
        for connection in self.connections:
            if connection.target is target:
                return True
        return False

    def other_node_pos(self, connection: UIConnection):
        if connection.source is self and connection.target is not None:
            return connection.target.ui_node.sceneBoundingRect().center()

        if connection.target is self:
            return connection.source.ui_node.sceneBoundingRect().center()

        return self.scene_center()

    def distance_from_cursor(self) -> float | None:
        scene = self.scene()
        if scene is None:
            return None

        view = scene.views()[0]
        cursor_pos = view.mapToScene(view.mapFromGlobal(QCursor.pos()))
        port_pos = self.mapToScene(0, 0)
        return QLineF(cursor_pos, port_pos).length()

    def view(self):
        scene = self.scene()
        if scene is None or not scene.views():
            return None
        return scene.views()[0]

    def start_distance_tracking(self, threshold: float = 25.0):
        self.threshold = threshold
        view = self.view()
        if view is None:
            return
        view.viewport().installEventFilter(self)
        self._tracking = True
        self._outside = False

    def stop_distance_tracking(self):
        view = self.view()
        if view is not None:
            view.viewport().removeEventFilter(self)
        self._tracking = False
        self._outside = False

    def eventFilter(self, obj, event):
        if not self._tracking:
            return super().eventFilter(obj, event)

        if event.type() == QEvent.Type.MouseMove and isinstance(event, QMouseEvent):
            view = self.view()
            if view is None:
                return False

            cursor_scene = view.mapToScene(event.position().toPoint())
            port_scene = self.mapToScene(QPointF(0, 0))
            distance = QLineF(cursor_scene, port_scene).length()
            dx = cursor_scene.x() - port_scene.x()
            dy = cursor_scene.y() - port_scene.y()

            if self.kind == "input":
                in_semicircle = dy <= 0
            else:
                in_semicircle = dy >= 0

            is_outside = (distance > self.threshold) or (not in_semicircle)
            if is_outside and not self._outside:
                self.stop_distance_tracking()
                self._outside = True
                self.moved_away.emit(self)
                self.refresh_connections()
            elif not is_outside:
                self._outside = False
                self.refresh_connections()

        return False

    def mousePressEvent(self, event):
        self.clicked.emit(self)
        event.accept()

    def hoverEnterEvent(self, event):
        self.hovered = True

        self.prepareGeometryChange()
        self.setScale(1.25)
        self.refresh_connections()
        self.update()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.hovered = False

        self.start_distance_tracking()
        self.prepareGeometryChange()
        self.setScale(1.0)
        self.refresh_connections()
        self.update()

        super().hoverLeaveEvent(event)