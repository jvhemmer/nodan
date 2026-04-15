from PySide6.QtCore import QPointF, QPoint
from PySide6.QtGui import QBrush, QColor, QPen, QPainterPath
from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsSimpleTextItem, QGraphicsPathItem, QGraphicsEllipseItem, \
    QGraphicsItem

import math

def connection_offset(index, count, spacing=8):
    center = (count - 1) / 2
    return (index - center) * spacing

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
        self.hovered = False

        self.setPos(x, y)
        self.setBrush(QBrush(QColor("#d08770") if kind == "input" else QColor("#a3be8c")))
        self.setPen(QPen(QColor("#2e3440"), 2))
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges)

        self.setAcceptHoverEvents(True)
        self.setTransformOriginPoint(self.rect().center())

    def scene_center(self):
        return self.mapToScene(self.rect().center())

    def add_connection(self, connection: Connection):
        if connection not in self.connections:
            self.connections.append(connection)

    def refresh_connections(self):
        for connection in self.connections:
            connection.update_path()

    def connection_anchor(self, connection):
        center = self.scene_center()

        if not self.hovered or connection not in self.connections:
            return center

        ordered = sorted(
            self.connections,
            key=lambda c: self.other_node_pos(c).x()
        )

        index = ordered.index(connection)
        count = len(ordered)

        radius = 14
        base_angle = -math.pi / 2  # up

        if count == 1:
            angle = base_angle
        else:
            max_spread = math.radians(120)

            used_spread = min(max_spread, math.radians(60 * (count - 1)))

            start = base_angle - used_spread / 2
            step = used_spread / (count - 1)
            angle = start + index * step

        return QPointF(
            center.x() + radius * math.cos(angle),
            center.y() + radius * math.sin(angle),
        )

    def other_node_pos(self, connection):
        if connection.source is self and connection.target is not None:
            return connection.target.parent.sceneBoundingRect().center()

        if connection.target is self:
            return connection.source.parent.sceneBoundingRect().center()

        return self.scene_center()

    def other_end_pos(self, connection):
        if connection.source is self:
            if connection.target is not None:
                return connection.target.scene_center()
            return connection.drag_pos

        if connection.target is self:
            return connection.source.scene_center()

        return None

    def side_of_connection(self, connection):
        center = self.scene_center()
        other = self.other_end_pos(connection)

        if other is None:
            return None

        dx = other.x() - center.x()
        dy = other.y() - center.y()

        if abs(dx) > abs(dy):
            return "right" if dx > 0 else "left"
        else:
            return "down" if dy > 0 else "up"

    def mousePressEvent(self, event):
        view = self.scene().views()[0]
        view.handle_port_click(self)
        event.accept()

    def hoverEnterEvent(self, event):
        self.hovered = True
        self.setScale(1.25)
        self.refresh_connections()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.hovered = False
        self.setScale(1.0)
        self.refresh_connections()
        super().hoverLeaveEvent(event)
