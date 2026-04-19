from __future__ import annotations
from typing import TYPE_CHECKING, Any

from ui.port import UIPort

if TYPE_CHECKING:
    from ui.canvas import Canvas

from PySide6.QtCore import QTimer, Signal
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton, QSizePolicy, QLayout, QBoxLayout, QLineEdit, \
    QLabel, QGridLayout

from ui.node import UINode
from ui.port_edit_row import PortEditRow, ACTIONS_COLUMN_WIDTH
from core.node_system import CoreNode


class NodeEditWindow(QWidget):
    evaluate_requested = Signal(CoreNode)
    add_input_requested = Signal(CoreNode)
    add_output_requested = Signal(object)

    def __init__(self, node: UINode, parent: Canvas):
        super().__init__()
        self.canvas = parent
        self.node = node
        self.rows = {}

        self.setWindowTitle(node.name)

        self.layout = QVBoxLayout(self)

        self.meta_box = QGroupBox("Node")
        self.meta_layout = QGridLayout(self.meta_box)
        self.name_label = QLabel("Name")
        self.name_edit = QLineEdit(self.node.name, self.meta_box)
        self.type_id_label = QLabel("Type")
        self.type_id_value = QLabel(node.core_node.definition.type_id)

        self.meta_layout.addWidget(self.name_label, 0, 0, 1, 1)
        self.meta_layout.addWidget(self.name_edit, 0, 1, 1, 1)
        self.meta_layout.addWidget(self.type_id_label, 1, 0, 1, 1)
        self.meta_layout.addWidget(self.type_id_value, 1, 1, 1, 1)

        self.input_box = QGroupBox("Inputs")
        self.input_layout = QVBoxLayout(self.input_box)

        self.output_box = QGroupBox("Outputs")
        self.output_layout = QVBoxLayout(self.output_box)

        self.add_input_button = QPushButton("Add Input")
        self.add_output_button = QPushButton("Add Output")

        self.evaluate_button = QPushButton("Evaluate node")

        self.layout.addWidget(self.meta_box)
        self.layout.addWidget(self.input_box)
        if node.core_node.definition.repeated_inputs:
            self.layout.addWidget(self.add_input_button)
        self.layout.addWidget(self.output_box)
        self.layout.addWidget(self.evaluate_button)

        self.add_input_button.clicked.connect(self.add_input)
        self.name_edit.editingFinished.connect(self.on_name_edit_changed)
        self.evaluate_button.clicked.connect(self.request_evaluation)

        self.rebuild_rows()

    def request_evaluation(self):
        self.evaluate_requested.emit(self.node.core_node)
        self.rebuild_rows()

    def rebuild_rows(self):
        self.rows.clear()

        while self.input_layout.count():
            item = self.input_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        while self.output_layout.count():
            item = self.output_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        self.input_layout.addWidget(self._build_port_header())
        self.output_layout.addWidget(self._build_port_header())

        for port in self.node.inputs:
            self.add_port_row(port)

        for port in self.node.outputs:
            self.add_port_row(port)

        QTimer.singleShot(0, self.adjustSize)

    def _build_port_header(self) -> QWidget:
        header = QWidget(self)
        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 0)

        name_label = QLabel("Name")
        type_label = QLabel("Type")
        value_label = QLabel("Value")
        actions_label = QLabel("Actions")

        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        type_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        actions_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(name_label, 2)
        layout.addWidget(type_label, 2)
        layout.addWidget(value_label, 2)
        actions_label.setFixedWidth(ACTIONS_COLUMN_WIDTH)
        layout.addWidget(actions_label)

        return header

    def add_port_row(self, port: UIPort):
        row = PortEditRow(port, self)
        row.set_value_editable(False)

        if port.is_editable() and not port.has_connection():
            row.set_value_editable(True)

        row.remove_requested.connect(self.remove_port)
        self.rows[port] = row

        if port.kind == "input":
            self.input_layout.addWidget(row)
        else:
            self.output_layout.addWidget(row)

        QTimer.singleShot(0, self.adjustSize)
        row.value_changed.connect(self.on_port_value_changed)

    def on_port_value_changed(self, port: UIPort, value: str):
        self.canvas.coordinator.set_port_value(port, value)

    def add_input(self):
        self.add_input_requested.emit(self.node.core_node)
        self.rebuild_rows()

    def remove_port(self, port):
        self.canvas.coordinator.remove_repeated_input(port)
        self.rebuild_rows()

    def on_name_edit_changed(self):
        # TODO: Change the CoreNode name as well
        self.node.change_label(self.name_edit.text())
        self.node.update()
        self.name_edit.clearFocus()
