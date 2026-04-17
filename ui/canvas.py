from PySide6.QtCore import QPoint, Qt, QPointF, QTimer
from PySide6.QtGui import QAction, QCursor
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QMenu

from ui.node import Node
from ui.port import Port
from ui.connection import Connection, ConnectionTip
from ui.node_edit_window import NodeEditWindow

class Canvas(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.alt_held = None
        self.setMouseTracking(True)

        self._is_panning = False
        self._pan_start = QPoint()
        self._zoom = 0
        self._zoom_step = 1.15

        self.nodes = []

        self.pending_connection: Connection | None = None
        self.pending_source_port = None

        self.node_edit_windows = []

        self._scene = QGraphicsScene()
        self.setScene(self._scene)

        self.setRenderHint(self.renderHints())
        self.setSceneRect(-2000, -2000, 4000, 4000)

        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)

        self._last_context_pos = QPoint()

    def get_cursor_pos(self) -> QPointF:
        return self.mapToScene(self.mapFromGlobal(QCursor.pos()))

    def add_node(self, pos: QPointF, name="New Node"):
        node = Node(self, pos.x(), pos.y(), name=name)

        self.scene().addItem(node)
        self.nodes.append(node)

    def remove_node(self, node: Node):
        if node in self.nodes:
            self.nodes.remove(node)

        self.scene().removeItem(node)

        node.delete()

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
        connection = Connection(port)
        connection.set_drag_pos(self.get_cursor_pos())
        self.scene().addItem(connection)

        self.pending_source_port = port
        self.pending_connection = connection

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

        if port.kind == 'input':
            # Prevent more than one connection to the same input
            if port.connections:
                return

        if port.node == self.pending_source_port.node:
            return

        # Clicking an unconnected input with a pending connection
        self.add_pending_connection(self.pending_connection, port)

    def set_show_port_names(self, value: bool):
        for node in self.nodes:
            for port in node.get_all_ports():
                if port.show_name != value:
                    port.show_name = value
                    port.update()

    # Key/Mouse Events
    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            item = self.itemAt(event.pos())
            if item is not None:
                if isinstance(item, Node):
                    w = NodeEditWindow(item)
                    w.show()
                    self.node_edit_windows.append(w)
                    event.accept()
                return

    def contextMenuEvent(self, event):
        # Right-click opens context menu
        item = self.itemAt(event.pos())
        if item is not None:
            super().contextMenuEvent(event)
            if event.isAccepted():
                return

        self._last_context_pos = event.pos()

        menu = QMenu()
        add_block_action = QAction("Add Node", self)
        menu.addAction(add_block_action)
        add_block_action.triggered.connect(self.add_node_at_context_pos)
        menu.exec(event.globalPos())

    def wheelEvent(self, event):
        # Zooming with Ctrl + Click
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

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.MiddleButton:
            self._is_panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
            return
        super().mouseReleaseEvent(event)

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
        super().mouseMoveEvent(event)

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

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Alt and not event.isAutoRepeat():
            self.set_show_port_names(True)
            event.accept()
            return
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key.Key_Alt and not event.isAutoRepeat():
            self.alt_held = False
            self.set_show_port_names(False)
            event.accept()
            return
        super().keyReleaseEvent(event)