from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QMenu

from ui.node import Node, Connection, Port

class Scene(QGraphicsScene):
    pass

class Canvas(QGraphicsView):
    def __init__(self):
        super().__init__()

        self.setMouseTracking(True)

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
        add_block_action.triggered.connect(self.add_block_at_context_pos)
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

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.MiddleButton:
            self._is_panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
            return

        super().mouseReleaseEvent(event)

    def add_block_at_context_pos(self):
        scene_pos = self.mapToScene(self._last_context_pos)
        block = Node(scene_pos.x(), scene_pos.y(), title="New Node")
        self.scene().addItem(block)

    def handle_port_click(self, port: Port):
        if self.pending_connection is None:
            if port.kind != "input":
                return

            self.pending_source_port = port
            self.pending_connection = Connection(port)
            self.scene().addItem(self.pending_connection)
            return

        if port is self.pending_source_port:
            self.scene().removeItem(self.pending_connection)
            self.pending_connection = None
            self.pending_source_port = None
            return

        if port.kind != "output":
            return

        self.pending_connection.set_target_port(port)
        self.pending_source_port.add_connection(self.pending_connection)
        port.add_connection(self.pending_connection)

        self.pending_connection = None
        self.pending_source_port = None
