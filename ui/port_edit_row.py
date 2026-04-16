from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QPushButton, QLabel

class PortEditRow(QWidget):
    remove_requested = Signal(object)

    def __init__(self, port, parent=None):
        super().__init__(parent)
        self.port = port

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.kind_label = QLabel(port.kind)
        self.name_edit = QLineEdit(port.name)
        self.remove_button = QPushButton("Remove")

        layout.addWidget(self.kind_label)
        layout.addWidget(self.name_edit, 1)
        layout.addWidget(self.remove_button)

        self.name_edit.editingFinished.connect(self.on_name_changed)
        self.remove_button.clicked.connect(self.on_remove_clicked)

    def on_name_changed(self):
        self.port.name = self.name_edit.text()
        self.port.update()
        self.name_edit.clearFocus()

    def on_remove_clicked(self):
        self.remove_requested.emit(self.port)