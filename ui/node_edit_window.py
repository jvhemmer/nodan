from __future__ import annotations
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ui.canvas import Canvas

from PySide6.QtCore import QTimer, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QGroupBox, QPushButton, QSizePolicy, QLayout, QBoxLayout, QLineEdit

from ui.node import UINode
from ui.port_edit_row import PortEditRow


class NodeEditWindow(QWidget):
    evaluate_requested = Signal(str)
    def __init__(self, node: UINode, parent: Canvas):
        super().__init__()
        self.canvas = parent
        self.node = node
        self.rows = {}

        self.setWindowTitle(node.name)

        self.layout = QVBoxLayout(self)

        self.meta_box = QGroupBox("Node")
        self.meta_layout = QVBoxLayout(self.meta_box)
        self.name_edit = QLineEdit(self.meta_box)
        self.meta_layout.addWidget(self.name_edit)

        self.input_box = QGroupBox("Inputs")
        self.input_layout = QVBoxLayout(self.input_box)

        self.output_box = QGroupBox("Outputs")
        self.output_layout = QVBoxLayout(self.output_box)

        self.add_input_button = QPushButton("Add Input")
        self.add_output_button = QPushButton("Add Output")

        self.evaluate_button = QPushButton("Evaluate node")

        self.layout.addWidget(self.meta_box)
        self.layout.addWidget(self.input_box)
        self.layout.addWidget(self.add_input_button)
        self.layout.addWidget(self.output_box)
        self.layout.addWidget(self.add_output_button)
        self.layout.addWidget(self.evaluate_button)

        self.add_input_button.clicked.connect(lambda: self.add_port("input"))
        self.add_output_button.clicked.connect(lambda: self.add_port("output"))
        self.name_edit.editingFinished.connect(self.on_name_edit_changed)
        self.evaluate_button.clicked.connect(lambda: self.evaluate_requested.emit(self.node.node_id))

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

        for port in self.node.inputs:
            self.add_port_row(port)

        for port in self.node.outputs:
            self.add_port_row(port)

        QTimer.singleShot(0, self.adjustSize)

    def add_port_row(self, port):
        row = PortEditRow(port, self)
        row.remove_requested.connect(self.remove_port)

        self.rows[port] = row

        if port.kind == "input":
            self.input_layout.addWidget(row)
        else:
            self.output_layout.addWidget(row)

        QTimer.singleShot(0, self.adjustSize)

    def add_port(self, kind):
        self.node.add_port(kind)
        self.rebuild_rows()

    def remove_port(self, port):
        self.node.remove_port(port)
        self.rebuild_rows()

    def on_name_edit_changed(self):
        self.node.change_label(self.name_edit.text())
        self.node.update()
        self.name_edit.clearFocus()