from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QPushButton, QLabel
from nodan.ui.port import UIPort
from nodan.core.node_system import format_data_type

ACTIONS_COLUMN_WIDTH = 90

class PortEditRow(QWidget):
    remove_requested = Signal(object)
    value_changed = Signal(object, str)

    def __init__(self, port: UIPort, parent=None):
        super().__init__(parent)
        self.port = port

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.name_edit = QLineEdit(port.name)
        self.type_value = QLabel(format_data_type(port.core_port.spec.data_type))
        self.type_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        value_text = "" if port.core_port.value is None else str(port.core_port.value)
        self.value_edit = QLineEdit(value_text)
        self.remove_button = QPushButton("Remove")
        self.remove_button.setFixedWidth(ACTIONS_COLUMN_WIDTH)

        layout.addWidget(self.name_edit, 2)
        layout.addWidget(self.type_value, 2)
        layout.addWidget(self.value_edit, 2)
        repeated = port.ui_node.core_node.definition.repeated_inputs
        is_repeated_input = (
            repeated is not None
            and port.kind == "input"
            and port.core_port.spec.name.startswith(repeated.base_name)
        )
        if is_repeated_input:
            layout.addWidget(self.remove_button)
        else:
            layout.addSpacing(ACTIONS_COLUMN_WIDTH)

        self.name_edit.editingFinished.connect(self.on_name_changed)
        self.value_edit.editingFinished.connect(self.on_value_changed)
        self.remove_button.clicked.connect(self.on_remove_clicked)

    def set_value_editable(self, editable: bool):
        self.value_edit.setEnabled(editable)

    def on_value_changed(self):
        self.value_changed.emit(self.port, self.value_edit.text())
        self.value_edit.clearFocus()

    def on_name_changed(self):
        self.port.name = self.name_edit.text()
        self.port.update()
        self.name_edit.clearFocus()

    def on_remove_clicked(self):
        self.remove_requested.emit(self.port)
