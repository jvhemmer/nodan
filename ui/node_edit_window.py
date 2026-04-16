from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QWidget, QVBoxLayout, QGroupBox, QPushButton, QSizePolicy, QLayout

from ui.node import Node
from ui.port_edit_row import PortEditRow

class NodeEditWindow(QWidget):
    def __init__(self, node: Node):
        super().__init__()
        self.node = node
        self.rows = {}

        self.setWindowTitle(node.name)
        # self.resize(400, 0)
        # self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)

        self.layout = QVBoxLayout(self)
        # self.layout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)

        self.input_box = QGroupBox("Inputs")
        self.input_layout = QVBoxLayout(self.input_box)

        self.output_box = QGroupBox("Outputs")
        self.output_layout = QVBoxLayout(self.output_box)

        self.add_input_button = QPushButton("Add Input")
        self.add_output_button = QPushButton("Add Output")

        self.layout.addWidget(self.input_box)
        self.layout.addWidget(self.add_input_button)
        self.layout.addWidget(self.output_box)
        self.layout.addWidget(self.add_output_button)

        self.add_input_button.clicked.connect(lambda: self.add_port("input"))
        self.add_output_button.clicked.connect(lambda: self.add_port("output"))

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

        print("window actual size", self.size())
        print("window", self.sizeHint(), self.minimumSizeHint())
        print("inputs box", self.input_box.sizeHint())
        print("outputs box", self.output_box.sizeHint())
        print("add input", self.add_input_button.sizeHint())
        print("add output", self.add_output_button.sizeHint())

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