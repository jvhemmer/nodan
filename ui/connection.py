from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ui.port import Port

from PySide6.QtCore import QPointF, QPoint, Qt
from PySide6.QtGui import QBrush, QColor, QPen, QPainterPath
from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsSimpleTextItem, QGraphicsPathItem, QGraphicsEllipseItem, \
    QGraphicsItem

import math

class ConnectionTip(QGraphicsEllipseItem):
    def __init__(self, parent):
        self.connection = parent
        radius = self.connection.thickness
        super().__init__(-radius, -radius, radius*2, radius*2, parent)

        self.hovered = False

        self.setPen(QPen(self.connection.color, self.connection.thickness))
        self.setBrush(self.connection.color)
        self.setZValue(1000)

        self.setAcceptedMouseButtons(Qt.MouseButton.LeftButton)
        self.setAcceptHoverEvents(True)

    def set_hovered(self, hovered: bool):
        if self.hovered == hovered:
            return

        self.hovered = hovered
        self.setScale(2 if hovered else 1.0)
        self.update()


class Connection(QGraphicsPathItem):
    def __init__(self, source: Port, target: Port | None=None):
        super().__init__()
        self.source = source
        self.target = target
        self.drag_pos = None
        self.hovered = False
        self.color = QColor("#88c0d0")
        self.thickness = 2
        self.highlight_thickness = 4
        self.tip = ConnectionTip(self)

        self.setPen(QPen(self.color, self.thickness))
        self.setZValue(-1)
        self.update_path()

        self.setAcceptHoverEvents(True)

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
        self.tip.setPos(end)

    def set_hovered(self, hovered: bool):
        if self.hovered == hovered:
            return

        self.hovered = hovered
        if hovered:
            if self.target is not None:
                # self.setZValue(100)
                self.setPen(QPen(self.color, self.highlight_thickness))
        else:
            # self.setZValue(-1)
            self.setPen(QPen(self.color, self.thickness))
        self.update()

    def hoverEnterEvent(self, event):
        self.set_hovered(True)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.set_hovered(False)
        super().hoverLeaveEvent(event)
    #
    # def update_tip_visibility(self):
    #     should_show = self.target is None or self.source.hovered
    #     self.tip.setVisible(should_show)

