from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QPushButton, QLabel

from nodan.ui.port import UIPort
from nodan.core.node_system import format_data_type
from nodan.ui.text_edit_window import TextEditWindow

ACTIONS_COLUMN_WIDTH = 180

class PortEditRow(QWidget):
    add_requested = Signal(object)
    remove_requested = Signal(object)
    value_changed = Signal(object, str)
    name_changed = Signal(object, str)

    def __init__(self, port: UIPort, parent):
        super().__init__()

        self.node_edit_window = parent
        self.port = port

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.name_edit = QLineEdit(port.name)
        self.type_value = QLabel(format_data_type(port.core_port.spec.data_type))
        self.type_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        value_text = "" if port.core_port.value is None else str(port.core_port.value)
        self.value_edit = QLineEdit(value_text)
        self.add_button = QPushButton("Add")
        self.edit_button = QPushButton("Edit")
        self.remove_button = QPushButton("Remove")
        self.actions_widget = QWidget(self)
        self.actions_layout = QHBoxLayout(self.actions_widget)
        self.actions_layout.setContentsMargins(0, 0, 0, 0)
        self.actions_layout.setSpacing(4)

        self.actions_layout.addWidget(self.add_button)
        self.actions_layout.addWidget(self.edit_button)

        layout.addWidget(self.name_edit, 2)
        layout.addWidget(self.type_value, 2)
        layout.addWidget(self.value_edit, 2)
        self.actions_layout.addWidget(self.remove_button)

        self.actions_widget.setFixedWidth(ACTIONS_COLUMN_WIDTH)
        layout.addWidget(self.actions_widget)

        can_add = port.ui_node.is_repeated_input(port)
        can_edit = port.kind == "input" and port.is_editable()
        can_remove = port.ui_node.is_repeated_input(port)

        self.add_button.setVisible(can_add)
        self.edit_button.setVisible(can_edit)
        self.remove_button.setVisible(can_remove)

        self.name_edit.editingFinished.connect(self.on_name_changed)
        self.value_edit.editingFinished.connect(self.on_value_changed)
        self.add_button.clicked.connect(self.on_add_clicked)
        self.edit_button.clicked.connect(self.on_edit_clicked)
        self.remove_button.clicked.connect(self.on_remove_clicked)

    def set_name_editable(self, editable: bool):
        self.name_edit.setReadOnly(not editable)

    def set_value_editable(self, editable: bool):
        self.value_edit.setEnabled(editable)

    def on_value_changed(self):
        self.value_changed.emit(self.port, self.value_edit.text())
        self.value_edit.clearFocus()

    def on_name_changed(self):
        self.name_changed.emit(self.port, self.name_edit.text())
        self.name_edit.clearFocus()

    def on_add_clicked(self):
        self.add_requested.emit(self.port)

    def on_edit_clicked(self):
        w = TextEditWindow(self.value_edit.text())
        w.show()
        w.editor.textChanged.connect(lambda: self.value_edit.setText(w.editor.toPlainText()))
        self.node_edit_window.value_editor_windows.append(w)

    def on_remove_clicked(self):
        self.remove_requested.emit(self.port)
