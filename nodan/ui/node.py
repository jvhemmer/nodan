from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import QEasingCurve, QRectF, Qt, Signal, QVariantAnimation
from PySide6.QtGui import QBrush, QColor, QFont, QPen
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QGraphicsItem,
    QGraphicsObject,
    QGraphicsRectItem,
    QGraphicsSimpleTextItem,
    QMenu,
)

from nodan.ui.node_port_row import UINodePortRow
from nodan.ui.port import UIPort

if TYPE_CHECKING:
    from nodan.core.node_system import CoreNode, CorePort
    from nodan.ui.canvas import Canvas


class UINode(QGraphicsRectItem):
    def __init__(
        self,
        parent: Canvas,
        core_node: CoreNode,
        x=0.0,
        y=0.0,
        width=380,
        height=140,
        name="Node",
    ):
        super().__init__(0, 0, width, height)
        self.canvas = parent
        self.core_node = core_node

        # State
        self.inputs: list[UIPort] = []
        self.outputs: list[UIPort] = []
        self._input_rows: dict[UIPort, UINodePortRow] = {}
        self._output_rows: dict[UIPort, UINodePortRow] = {}
        self._last_context_pos = None
        self.name = name
        self._show_hideable_inputs = False
        self._animated_hidden_rows = 0.0

        # Geometry
        self._corner_radius = 8
        self._content_margin = 16
        self._title_height = 26
        self._body_top_gap = 6
        self._row_height = 24
        self._horizontal_gap = 12
        self._field_height = 20
        self._min_label_width = 60
        self._field_width = 100

        # Colors
        self._outline_color = QColor("#262626")
        self._selected_outline_color = QColor("#5a5a5a")
        self._header_color = QColor("#262626")
        self._selected_header_color = QColor("#5a5a5a")
        self._outline_pen = QPen(self._outline_color, 2)
        self._text_brush = QBrush(QColor("#eceff4"))
        self._fill_brush = QBrush(QColor("#1e1e1e"))


        # Buttons
        # TODO: Find a way for the coordinator to never be None
        self.delete_button = UINodeButton(self, "/x_filled.svg", "/x_outline.svg")
        self.delete_button.clicked.connect(
            lambda: self.canvas.coordinator.remove_node(self.core_node.id)
        )
        self.delete_button.setVisible(False)

        self.eval_button = UINodeButton(self, "/play_filled.svg", "/play_outline.svg")
        self.eval_button.clicked.connect(
            lambda: self.canvas.coordinator.evaluate_node(self.core_node)
        )
        self.eval_button.setVisible(False)

        # Animations
        self._hover_animation = QVariantAnimation()
        self._hover_animation.setDuration(180)
        self._hover_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._hover_animation.valueChanged.connect(self._on_hover_animation_changed)

        # Initialize
        self.setPos(x, y)
        self.setFlags(
            QGraphicsRectItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsRectItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsRectItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self.setBrush(self._fill_brush)
        self.setPen(self._outline_pen)
        self.title = QGraphicsSimpleTextItem(self)
        self.title.setBrush(self._text_brush)
        self.change_label(name)
        self.setAcceptHoverEvents(True)

    # === Paint ===
    def paint(self, painter, option, widget=None):
        outline_color = (
            self._selected_outline_color if self.isSelected() else self._outline_color
        )
        header_color = (
            self._selected_header_color if self.isSelected() else self._header_color
        )

        painter.setBrush(self.brush())
        painter.setPen(QPen(outline_color, self.pen().widthF()))
        painter.drawRoundedRect(self.rect(), self._corner_radius, self._corner_radius)

        painter.setBrush(header_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(
            0,
            0,
            self.rect().width(),
            self._title_height,
            self._corner_radius,
            self._corner_radius,
        )
        painter.drawRect(
            0, self._title_height / 2, self.rect().width(), self._title_height / 2
        )

    # === Geometry ===
    def _compute_label_width(self) -> float:
        labels = [self._min_label_width]
        for row in self._input_rows.values():
            labels.append(row.label_width())
        for row in self._output_rows.values():
            labels.append(row.label_width())
        return max(labels)

    def _compute_field_width(self) -> float:
        widths = [self._field_width]
        for row in self._input_rows.values():
            widths.append(row.field_width_hint())
        for row in self._output_rows.values():
            widths.append(row.field_width_hint())
        return max(widths)

    # === Layout ===
    def layout_ports(self):
        rows = max(
            len(self._base_visible_inputs())
            + self._animated_hidden_rows
            + len(self.outputs),
            1,
        )
        label_width = self._compute_label_width()
        field_width = self._compute_field_width()
        content_width = (
            self._content_margin
            + label_width
            + self._horizontal_gap
            + field_width
            + self._content_margin
        )
        title_width = self.title.boundingRect().width() + (self._content_margin * 2)
        buttons_width = sum(b.boundingRect().width() for b in self.get_all_buttons())
        width = max(content_width, title_width + buttons_width)
        height = (
            self._title_height
            + self._body_top_gap
            + (rows * self._row_height)
            + self._content_margin / 2
        )
        self.setRect(0, 0, width, height)

        self._layout_title()
        self._layout_inputs(label_width, field_width)
        self._layout_outputs(label_width, field_width)
        self.sync_port_widgets()
        self.layout_buttons()

    def _layout_inputs(self, label_width: float, field_width: float) -> None:
        ordered_inputs = sorted(
            self.inputs,
            key=lambda port: port.core_port.spec.hideable,
        )
        visible_index = 0
        hidden_index = 0
        for port in ordered_inputs:
            if self._is_hidden_candidate(port):
                opacity = max(0.0, min(1.0, self._animated_hidden_rows - hidden_index))
                is_visible = self._show_hideable_inputs or opacity > 0.0
                self._set_input_row_state(port, is_visible, opacity)
                if not is_visible:
                    hidden_index += 1
                    continue
            else:
                self._set_input_row_state(port, True, 1.0)
                opacity = 1.0

            if not opacity:
                hidden_index += 1
                continue

            row_center_y = (
                self._title_height
                + self._body_top_gap
                + (visible_index * self._row_height)
                + (self._row_height / 2)
            )
            port.setPos(0, row_center_y)
            self._input_rows[port].set_geometry(
                self._content_margin,
                row_center_y,
                self._content_margin + label_width + self._horizontal_gap,
                field_width,
                self._field_height,
            )
            port.refresh_connections()
            visible_index += 1
            if self._is_hidden_candidate(port):
                hidden_index += 1

    def _layout_outputs(self, label_width: float, field_width: float) -> None:
        right_edge = self.rect().width()
        label_x = self._content_margin
        value_x = self._content_margin + label_width + self._horizontal_gap

        for index, port in enumerate(self.outputs):
            row_index = (
                len(self._base_visible_inputs()) + self._animated_hidden_rows + index
            )
            row_center_y = (
                self._title_height
                + self._body_top_gap
                + (row_index * self._row_height)
                + (self._row_height / 2)
            )
            port.setPos(right_edge, row_center_y)
            self._output_rows[port].set_geometry(
                label_x,
                row_center_y,
                value_x,
                field_width,
                self._field_height,
            )
            port.refresh_connections()

    def _layout_title(self) -> None:
        title_rect = self.title.boundingRect()
        title_y = (self._title_height - title_rect.height()) / 2
        self.title.setPos(self._content_margin, title_y)

    def sync_port_widgets(self) -> None:
        for row in self._input_rows.values():
            row.sync()
        for row in self._output_rows.values():
            row.sync()

    def _base_visible_inputs(self) -> list[UIPort]:
        return [
            port
            for port in self.inputs
            if not self._is_hidden_candidate(port)
        ]

    def _hidden_candidate_inputs(self) -> list[UIPort]:
        return [port for port in self.inputs if self._is_hidden_candidate(port)]

    def _is_hidden_candidate(self, port: UIPort) -> bool:
        return port.core_port.spec.hideable and not port.has_connection()

    def _set_input_row_state(
        self, port: UIPort, visible: bool, opacity: float = 1.0
    ) -> None:
        row = self._input_rows[port]
        port.setVisible(visible)
        row.label_item.setVisible(visible)
        row.proxy.setVisible(visible)
        port.setOpacity(opacity)
        row.label_item.setOpacity(opacity)
        row.proxy.setOpacity(opacity)

    # === Port management ===
    def add_port(self, kind: str, core_port: CorePort) -> UIPort:
        port = UIPort(self, kind, core_port, 0, 0, name=core_port.spec.name)
        if kind == "input":
            self.inputs.append(port)
            self._input_rows[port] = UINodePortRow(self, port)
        else:
            self.outputs.append(port)
            self._output_rows[port] = UINodePortRow(self, port)
        self.register_port(port)
        self.layout_ports()
        return port

    def remove_port(self, port: UIPort):
        ports = self.inputs if port.kind == "input" else self.outputs
        if port not in ports:
            return

        for connection in port.connections.copy():
            connection.delete()

        ports.remove(port)

        rows = self._input_rows if port.kind == "input" else self._output_rows
        row = rows.pop(port)
        scene = self.scene()
        if scene is not None:
            row.delete()
            scene.removeItem(port)

        self.layout_ports()

    def register_port(self, port: UIPort):
        port.clicked.connect(self.canvas.handle_port_click)

    def get_all_ports(self) -> list[UIPort]:
        return [*self.inputs, *self.outputs]

    # === Button management ===
    def layout_buttons(self):
        buttons = self.get_all_buttons()
        for i, button in enumerate(buttons):
            x_pos = self.rect().width() - (i + 1) * button.boundingRect().width()
            button.setPos(x_pos, 0)

    def get_all_buttons(self) -> list[UINodeButton]:
        buttons = [
            child for child in self.childItems() if isinstance(child, UINodeButton)
        ]
        return buttons

    # Key/Mouse events
    def contextMenuEvent(self, event):
        self._last_context_pos = event.pos()

        menu = QMenu()
        delete_node = menu.addAction("Delete node")

        chosen = menu.exec(event.screenPos())

        if chosen == delete_node:
            self.canvas.coordinator.remove_node(self.core_node.id)

        event.accept()

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            for port in self.get_all_ports():
                for connection in port.connections:
                    connection.update_path()
        elif change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            self.update()
        return super().itemChange(change, value)

    def hoverEnterEvent(self, event):
        self._show_hideable_inputs = True
        self._start_hover_animation(True)
        for button in self.get_all_buttons():
            button.setVisible(True)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self._show_hideable_inputs = False
        self._start_hover_animation(False)
        for button in self.get_all_buttons():
            button.setVisible(False)
        super().hoverLeaveEvent(event)

    # === Animations ===
    def _start_hover_animation(self, expanded: bool) -> None:
        hidden_count = len(self._hidden_candidate_inputs())
        target = float(hidden_count if expanded else 0)
        self._hover_animation.stop()
        self._hover_animation.setStartValue(self._animated_hidden_rows)
        self._hover_animation.setEndValue(target)
        self._hover_animation.start()

    def _on_hover_animation_changed(self, value) -> None:
        self._animated_hidden_rows = float(value)
        self.layout_ports()

    # === Helpers ===
    def change_label(self, label: str):
        self.name = label
        self.title.setText(label)
        font = QFont("Arial", 10)
        font.setBold(True)
        font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
        font.setHintingPreference(QFont.HintingPreference.PreferNoHinting)
        self.title.setFont(font)
        self._layout_title()
        self.layout_ports()

    def delete(self):
        for port in self.get_all_ports():
            self.remove_port(port)


class UINodeButton(QGraphicsObject):
    clicked = Signal()

    def __init__(self, parent: UINode, on_svg: str, off_svg: str):
        super().__init__(parent)
        self.ui_node: UINode = parent

        self._on_svg = on_svg
        self._off_svg = off_svg

        self.renderer = QSvgRenderer()
        self.box_size = self.ui_node._title_height
        self._rect = QRectF(0, 0, self.box_size, self.box_size)

        self.setAcceptHoverEvents(True)
        self.set_icon(off_svg)

    # === Painting ===
    def boundingRect(self):
        return self._rect

    def paint(self, painter, option, widget=None):
        self.renderer.render(painter, self.boundingRect())

    # === Key/Mouse press events
    def mousePressEvent(self, event):
        self.clicked.emit()
        event.accept()

    def hoverEnterEvent(self, event):
        self.set_icon(self._on_svg)

    def hoverLeaveEvent(self, event):
        self.set_icon(self._off_svg)

    # === Helpers ===
    def set_icon(self, file_name: str) -> None:
        icon_path = str(Path(__file__).resolve().parents[1] / "assets" / "icons")
        self.renderer.load(icon_path + file_name)
        self.update()
