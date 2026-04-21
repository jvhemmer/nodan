from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nodan.ui.node import UINode
    from nodan.ui.connection import UIConnection

from PySide6.QtCore import QPointF, Signal, QRectF, QLineF, QEvent
from PySide6.QtGui import QBrush, QColor, QCursor, QMouseEvent, QPainter
from PySide6.QtWidgets import QGraphicsObject, QGraphicsItem

from nodan.core.node_system import CorePort

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

        self.connections = []

        self.text_painter = QPainter()

        self.hovered = False
        self.threshold = 25
        self._tracking = False
        self._outside = False
        self.show_name = False

        self._connected_brush = QBrush(QColor("#a3be8c"))
        self._empty_editable_brush = QBrush(QColor("#81A1C1"))
        self._filled_editable_brush = QBrush(QColor("#262626"))
        self._output_brush = QBrush(QColor("#d08770"))

        self.setPos(x, y)
        self.setZValue(1)
        self.setAcceptHoverEvents(True)

    def boundingRect(self):
        r = self.radius
        return QRectF(-r, -r, r * 2, r * 2)

    def draw_name(self, painter):
        return

    def paint(self, painter, option, widget=None):
        if self.kind == "input":
            if not self.is_editable():
                painter.setBrush(self._connected_brush)
            elif self.has_connection():
                painter.setBrush(self._connected_brush)
            elif self.has_assigned_value():
                painter.setBrush(self._filled_editable_brush)
            else:
                painter.setBrush(self._empty_editable_brush)
        else:
            painter.setBrush(self._output_brush)

        painter.setPen(self.ui_node._outline_pen)
        painter.drawEllipse(self.boundingRect())
        if self.hovered or self.show_name:
            self.draw_name(painter)

    def is_editable(self) -> bool:
        return self.core_port.spec.editable

    def has_connection(self) -> bool:
        connected = False
        if self.connections:
            connected = True
        return connected

    def has_assigned_value(self) -> bool:
        return self.core_port.value is not None

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

        if connection not in self.connections:
            return center

        if not self.hovered and not self._tracking:
            return center

        if not self.hovered and self._outside:
            return center

        ordered = sorted(
            self.connections,
            key=lambda c: self.other_node_pos(c).y()
        )
        index = ordered.index(connection)
        count = len(ordered)

        radius = 18 + ((count - 1) * 1)
        base_angle = 0 if self.kind == "output" else np.pi

        if count == 1:
            angle = base_angle
        else:
            max_spread = np.radians(100)
            used_spread: float = min(max_spread, np.radians(35 * (count - 1)))
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

            if self.kind == "input":
                in_semicircle = dx <= 0
            else:
                in_semicircle = dx >= 0

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
