from PySide6.QtCore import QPoint, Qt, QPointF, QObject
from PySide6.QtGui import QAction, QMouseEvent, QCursor
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QMenu

from ui.node import Node
from ui.port import Port
from ui.connection import Connection, ConnectionTip

class Scene(QGraphicsScene):
    pass

class Canvas(QGraphicsView):
    def __init__(self):
        super().__init__()

        self.setMouseTracking(True)

        self._hovered_items = set()
        self._is_panning = False
        self._pan_start = QPoint()
        self._zoom = 0
        self._zoom_step = 1.15

        self.pending_connection: Connection | None = None
        self.pending_source_port = None

        self._scene = QGraphicsScene()
        self.setScene(self._scene)

        self.setRenderHint(self.renderHints())
        self.setSceneRect(-2000, -2000, 4000, 4000)

        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)

        self._last_context_pos = QPoint()

    # Right-click -> context menu
    def contextMenuEvent(self, event):
        self._last_context_pos = event.pos()

        menu = QMenu()
        add_block_action = QAction("Add Node", self)
        menu.addAction(add_block_action)
        add_block_action.triggered.connect(self.add_node_at_context_pos)
        menu.exec(event.globalPos())

    # Zooming with Ctrl + Click
    def wheelEvent(self, event):
        modifiers = event.modifiers()
        delta = event.angleDelta().y()

        if modifiers & Qt.KeyboardModifier.ControlModifier:
            self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

            if delta > 0:
                factor = self._zoom_step
            else:
                factor = 1/self._zoom_step

            self.scale(factor, factor)

        event.accept()
        return

    def mousePressEvent(self, event):
        # Panning with MMB
        if event.button() == Qt.MouseButton.MiddleButton:
            self._is_panning = True
            self._pan_start = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
            return

        if self.pending_connection is not None:
            item = self.itemAt(event.pos())
            if item in (self.pending_connection, self.pending_connection.tip):
                self.pending_connection.delete()
                self.pending_connection = None
                self.pending_source_port = None
                event.accept()

        if self.pending_connection is None:
            scene_pos = self.mapToScene(event.pos())
            items = self.scene().items(scene_pos)
            for item in items:
                if isinstance(item, Connection):
                    self.detach_connection(item)
                    event.accept()
                    return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        # Move the connection with mouse
        if self.pending_connection is not None:
            scene_pos = self.mapToScene(event.pos())
            self.pending_connection.set_drag_pos(scene_pos)

        # Panning
        if self._is_panning:
            delta = event.pos() - self._pan_start
            self._pan_start = event.pos()

            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - delta.x()
            )
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - delta.y()
            )
            event.accept()
            return

        # Hovering over Ports or ConnectionTips
        scene_pos = self.mapToScene(event.pos())
        items_under_cursor = self.scene().items(scene_pos)
        self.handle_port_or_connection_hover(items_under_cursor)

        super().mouseMoveEvent(event)

    def get_cursor_pos(self) -> QPointF:
        return self.mapToScene(self.mapFromGlobal(QCursor.pos()))

    def handle_port_or_connection_hover(self, items):
        # TODO: Make Node, Port and Connection inherit from QGraphicsObject and customize hover behavior
        hovered_items = set()

        for item in items:
            if isinstance(item, Port):
                hovered_items.add(item)
            elif isinstance(item, ConnectionTip):
                if item.connection.target is not None:
                    hovered_items.add(item.connection.target)
                    hovered_items.add(item.connection)
                    hovered_items.add(item)

        for item in self._hovered_items - hovered_items:
            item.set_hovered(False)

        for item in hovered_items - self._hovered_items:
            item.set_hovered(True)

        self._hovered_items = hovered_items

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.MiddleButton:
            self._is_panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def add_node(self, pos: QPointF, title="New Node"):
        node = Node(pos.x(), pos.y(), title=title)

        node.input.clicked.connect(self.handle_port_click)
        node.output.clicked.connect(self.handle_port_click)

        self.scene().addItem(node)

    def add_node_at_context_pos(self):
        scene_pos = self.mapToScene(self._last_context_pos)
        self.add_node(scene_pos)

    def add_pending_connection(self, connection: Connection, target: Port):
        source = self.pending_source_port

        connection.set_target_port(target)
        connection.tip.clicked.connect(self.detach_connection)
        source.add_connection(connection)
        target.add_connection(connection)
        # print(f"Connected to {target.parent.label.text()}")
        self.clear_pending_connection()

    def detach_connection(self, connection: Connection):
        source = connection.source
        connection.delete()
        self.start_pending_connection(source)

    def start_pending_connection(self, port: Port):
        # print(f"Started connection from {port.parent.label.text()}")
        self.pending_source_port = port
        self.pending_connection = Connection(port)
        self.scene().addItem(self.pending_connection)
        self.pending_connection.set_drag_pos(self.get_cursor_pos())

    def clear_pending_connection(self):
        self.pending_connection = None
        self.pending_source_port = None

    def cancel_pending_connection(self) -> None:
        if self.pending_connection is not None:
            # print(f"Canceled connection from {self.pending_connection.source.parent.label.text()}")
            self.scene().removeItem(self.pending_connection)
            self.clear_pending_connection()

    def handle_port_click(self, port: Port):
        if self.pending_connection is None:
            # Start a connection if clicked on an input
            if port.kind != "output":
                return
            self.start_pending_connection(port)
            return

        if port is self.pending_source_port:
            # If clicking on the same port, cancel
            self.cancel_pending_connection()
            return

        if port.kind != "input":
            # Clicking an output without a pending connection
            return

        if self.pending_source_port.is_connected_to(port):
            # Prevent recreating an existing connection
            return

        # Clicking an output with a pending connection
        self.add_pending_connection(self.pending_connection, port)