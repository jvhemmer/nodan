from __future__ import annotations
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from nodan.ui.port import UIPort

from PySide6.QtCore import QPointF, QPoint, Qt, QRectF, Signal
from PySide6.QtGui import QColor, QPen, QPainterPath
from PySide6.QtWidgets import QGraphicsPathItem, QGraphicsObject


class UIConnectionTip(QGraphicsObject):
    clicked = Signal(object)
    def __init__(self, parent: UIConnection):
        super().__init__(parent)

        self.connection: UIConnection = parent
        self.radius = self.connection.thickness
        self.hovered = False

        self.setZValue(100)
        self.setAcceptedMouseButtons(Qt.MouseButton.LeftButton)
        self.setAcceptHoverEvents(True)

    def boundingRect(self):
        r = self.radius
        return QRectF(-r, -r, r * 2, r * 2)

    def paint(self, painter, option, widget=None):
        painter.setPen(QPen(self.connection.color, self.connection.thickness))
        painter.setBrush(self.connection.color)
        painter.drawEllipse(self.boundingRect())

    def mousePressEvent(self, event):
        self.clicked.emit(self.connection)
        event.accept()

    def hoverEnterEvent(self, event):
        self.hovered = True
        if self.connection.target:
            self.setScale(2.0)
        self.update()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.hovered = False
        self.setScale(1.0)
        self.update()

class UIConnection(QGraphicsPathItem):
    def __init__(self, source: UIPort, target: UIPort | None=None):
        super().__init__()
        self.source = source
        self.target = target
        self.drag_pos = None
        self.hovered = False
        self.color = QColor("#88c0d0")
        self.thickness = 2
        self.highlight_thickness = 4
        self.tip = UIConnectionTip(self)

        self.setPen(QPen(self.color, self.thickness))
        self.setZValue(-1)
        self.update_path()

        self.setAcceptHoverEvents(True)

    def set_drag_pos(self, pos: QPoint | QPointF):
        self.drag_pos = pos
        self.update_path()

    def set_target_port(self, port: UIPort):
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

    def calculate_offset(self) -> tuple[float, float]:
        source = self.source
        target = self.target

        if not target:
            return 40, 0

        source_pos = source.scenePos()
        target_pos = target.scenePos()

        dx = target_pos.x() - source_pos.x()
        dy = target_pos.y() - source_pos.y()
        if dx < 0:
            # TODO: Improve offset calculation
            return 40 + 10*np.sqrt(abs(dx)), 10*np.sqrt(abs(dy))
        else:
            return 40, 0

    def update_path(self):
        start = self.source.connection_anchor(self)

        if self.target is not None:
            end = self.target.connection_anchor(self)
        elif self.drag_pos is not None:
            end = self.drag_pos
        else:
            end = start

        offset_x, offset_y = self.calculate_offset()

        path = QPainterPath(start)
        path.cubicTo(
            QPointF(start.x() + offset_x, start.y() + offset_y),
            QPointF(end.x() - offset_x, end.y() - offset_y),
            end,
        )
        self.setPath(path)
        self.tip.setPos(end)
        self.update()

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

