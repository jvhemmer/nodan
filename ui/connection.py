from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ui.port import Port

from PySide6.QtCore import QPointF, QPoint
from PySide6.QtGui import QBrush, QColor, QPen, QPainterPath
from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsSimpleTextItem, QGraphicsPathItem, QGraphicsEllipseItem, \
    QGraphicsItem

import math

class Connection(QGraphicsPathItem):
    def __init__(self, source: Port, target: Port | None=None):
        super().__init__()
        self.source = source
        self.target = target
        self.drag_pos = None

        self.setPen(QPen(QColor("#88c0d0"), 2))
        self.setZValue(-1)
        self.update_path()

    def set_drag_pos(self, pos: QPoint | QPointF):
        self.drag_pos = pos
        self.update_path()

    def set_target_port(self, port: Port):
        self.target = port
        self.drag_pos = None
        self.update_path()

    def delete(self):
        if self.source is not None and self in self.source.connections:
            self.source.connections.remove(self)

        if self.target is not None and self in self.target.connections:
            self.target.connections.remove(self)

        scene = self.scene()
        if scene is not None:
            scene.removeItem(self)

        self.source = None
        self.target = None
        self.drag_pos = None

    def update_path(self):
        start = self.source.connection_anchor(self)

        if self.target is not None:
            end = self.target.connection_anchor(self)
        elif self.drag_pos is not None:
            end = self.drag_pos
        else:
            end = start

        offset = 80

        path = QPainterPath(start)
        path.cubicTo(
            QPointF(start.x(), start.y() + offset),
            QPointF(end.x(), end.y() - offset),
            end,
        )
        self.setPath(path)


