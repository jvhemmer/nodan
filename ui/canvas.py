from __future__ import annotations
from typing import TYPE_CHECKING

from core.node_system import Operation

if TYPE_CHECKING:
    from coordinator.coordinator import Coordinator

from PySide6.QtCore import QPoint, Qt, QPointF, Signal
from PySide6.QtGui import QCursor, QPainter
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QMenu

from ui.node import UINode
from ui.port import UIPort
from ui.connection import UIConnection, UIConnectionTip
from ui.node_edit_window import NodeEditWindow


class Canvas(QGraphicsView):
    add_node_requested = Signal(str, QPointF)
    port_clicked = Signal()
    def __init__(self):
        super().__init__()
        self.coordinator: Coordinator | None = None
        self.alt_held = None
        self.setMouseTracking(True)

        self._is_panning = False
        self._pan_start = QPoint()
        self._zoom = 0
        self._zoom_step = 1.15

        self.nodes = []

        self.pending_connection: UIConnection | None = None
        self.pending_source_port: UIPort | None = None

        self.node_edit_windows = []

        self._scene = QGraphicsScene()
        self.setScene(self._scene)

        self.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.setSceneRect(-2000, -2000, 4000, 4000)

        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)

        self._last_context_pos = QPoint()

    # === Nodes ===
    def remove_node(self, node: UINode):
        if node in self.nodes:
            self.nodes.remove(node)

        self.scene().removeItem(node)
        node.delete()

    def add_node_at_context_pos(self, node_type: str):
        scene_pos = self.mapToScene(self._last_context_pos)
        self.add_node_requested.emit(node_type, scene_pos)

    # === Connections ===
    def fulfill_pending_connection(self, connection: UIConnection, target: UIPort):
        if self.pending_source_port:
            source = self.pending_source_port
        else:
            raise ValueError("Attempted to connect without a source port.")
        connection.set_target_port(target)
        connection.tip.clicked.connect(self.detach_connection)
        source.add_connection(connection)
        target.add_connection(connection)
        self.clear_pending_connection()

    def detach_connection(self, connection: UIConnection):
        source = connection.source
        target = connection.target

        if not self.coordinator:
            raise ValueError("Canvas must have a reference to Coordinator prior to UI initialization.")

        if target:
            self.coordinator.disconnect_ports(source, target)

        connection.delete()
        self.start_pending_connection(source)

    def start_pending_connection(self, port: UIPort):
        connection = UIConnection(port)
        connection.set_drag_pos(self.get_cursor_pos())
        self.scene().addItem(connection)

        self.pending_source_port = port
        self.pending_connection = connection

    def clear_pending_connection(self):
        self.pending_connection = None
        self.pending_source_port = None

    def cancel_pending_connection(self) -> None:
        if self.pending_connection is not None:
            self.scene().removeItem(self.pending_connection)
            self.clear_pending_connection()

    # === Ports ===
    def handle_port_click(self, port: UIPort):
        if self.pending_connection is None:
            # If there's no pending connection
            if port.kind != "output":
                return
            self.start_pending_connection(port)
            return

        if port is self.pending_source_port:
            # Clicking on the source port
            self.cancel_pending_connection()
            return

        source = self.pending_source_port
        target = port

        if not self.coordinator:
            raise ValueError("Canvas must have a reference to Coordinator prior to UI initialization.")

        if not self.coordinator.can_connect(source, target):
            return

        self.pending_connection.delete()
        self.clear_pending_connection()
        self.coordinator.connect_ports(source, target)

    def set_show_port_names(self, value: bool):
        for node in self.nodes:
            for port in node.get_all_ports():
                if port.show_name != value:
                    port.show_name = value
                    port.update()

    # === Key/Mouse Events ===
    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            item = self.itemAt(event.pos())
            if item is not None:
                if isinstance(item, UINode):
                    w = NodeEditWindow(item, self)
                    w.show()
                    self.node_edit_windows.append(w)
                    w.evaluate_requested.connect(self.coordinator.evaluate_node)
                    w.add_input_requested.connect(self.coordinator.add_repeated_input)
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

        for type_id, op_cls in Operation.registry.items():
            action = menu.addAction(f"Add {op_cls.title} node")
            action.triggered.connect(lambda checked=False,node_type=type_id: self.add_node_at_context_pos(node_type))

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
                if isinstance(item, UIConnectionTip):
                    self.detach_connection(item.connection)
                    event.accept()
                    return
                if isinstance(item, UIConnection):
                    break

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

    # === Helpers ===
    def get_cursor_pos(self) -> QPointF:
        return self.mapToScene(self.mapFromGlobal(QCursor.pos()))
