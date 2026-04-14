from PySide6.QtCore import QPointF
from PySide6.QtGui import QBrush, QColor, QPen, QPainterPath
from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsSimpleTextItem, QGraphicsPathItem, QGraphicsEllipseItem, \
    QGraphicsItem


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

        label = QGraphicsSimpleTextItem(title, self)
        label.setBrush(QBrush(QColor("#eceff4")))
        label.setPos(12, 10)

        self.input = Port(self, "input", x=width/2, y=height)
        self.output = Port(self, "output", x=width/2, y=0)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            for port in (self.input, self.output):
                for connection in port.connections:
                    connection.update_path()
        return super().itemChange(change, value)



class Connection(QGraphicsPathItem):
    def __init__(self, source, target=None):
        super().__init__()
        self.source = source
        self.target = target
        self.drag_pos = None

        self.setPen(QPen(QColor("#88c0d0"), 3))
        self.setZValue(-1)
        self.update_path()

    def set_drag_pos(self, pos):
        self.drag_pos = pos
        self.update_path()

    def set_target_port(self, port):
        self.target = port
        self.drag_pos = None
        self.update_path()

    def update_path(self):
        start = self.source.scene_center()

        if self.target is not None:
            end = self.target.scene_center()
        elif self.drag_pos is not None:
            end = self.drag_pos
        else:
            end = start

        offset = 80

        # dy = (end.y() - start.y()) * 0.5

        path = QPainterPath(start)
        path.cubicTo(
            QPointF(start.x(), start.y() + offset),
            QPointF(end.x(), end.y() - offset),
            end,
        )
        self.setPath(path)

class Port(QGraphicsEllipseItem):
    def __init__(self, parent: Node, kind, x, y, radius=6):
        super().__init__(-radius, -radius, radius*2, radius*2, parent)
        self.parent = parent
        self.kind = kind
        self.connections = []

        self.setPos(x, y)
        self.setBrush(QBrush(QColor("#d08770") if kind == "input" else QColor("#a3be8c")))
        self.setPen(QPen(QColor("#2e3440"), 2))
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges)

    def scene_center(self):
        return self.mapToScene(self.rect().center())

    def add_connection(self, connection):
        if connection not in self.connections:
            self.connections.append(connection)

    def mousePressEvent(self, event):
        view = self.scene().views()[0]
        view.handle_port_click(self)
        event.accept()
