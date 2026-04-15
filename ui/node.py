from PySide6.QtCore import QPointF, QPoint
from PySide6.QtGui import QBrush, QColor, QPen, QPainterPath
from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsSimpleTextItem, QGraphicsPathItem, QGraphicsEllipseItem, \
    QGraphicsItem, QWidget

import math

from ui.port import Port
from ui.connection import Connection

class Node(QGraphicsRectItem):
    def __init__(self, x=0, y=0, width=140, height=70, title="Node"):
        super().__init__(0, 0, width, height)
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

        self.input = Port(self, "input", x=width/2, y=0)
        self.output = Port(self, "output", x=width/2, y=height)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            for port in (self.input, self.output):
                for connection in port.connections:
                    connection.update_path()
        return super().itemChange(change, value)