from typing import Any

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QPushButton, QLabel
from ui.port import UIPort

class PortEditRow(QWidget):
    remove_requested = Signal(object)
    value_changed = Signal(object, str)

    def __init__(self, port: UIPort, parent=None):
        super().__init__(parent)
        self.port = port

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # self.kind_label = QLabel(port.kind)
        self.name_label = QLabel("Name")
        self.name_edit = QLineEdit(port.name)
        self.value_label = QLabel("Value")
        self.value_edit = QLineEdit(port.core_port.value)
        self.remove_button = QPushButton("Remove")

        # layout.addWidget(self.kind_label)
        layout.addWidget(self.name_label, 1)
        layout.addWidget(self.name_edit, 1)
        layout.addWidget(self.value_label, 1)
        layout.addWidget(self.value_edit, 1)
        layout.addWidget(self.remove_button)

        self.name_edit.editingFinished.connect(self.on_name_changed)
        self.value_edit.editingFinished.connect(self.on_value_changed)
        self.remove_button.clicked.connect(self.on_remove_clicked)

    def on_value_changed(self):
        self.value_changed.emit(self.port, self.value_edit.text())

    def on_name_changed(self):
        self.port.name = self.name_edit.text()
        self.port.update()
        self.name_edit.clearFocus()

    def on_remove_clicked(self):
        self.remove_requested.emit(self.port)