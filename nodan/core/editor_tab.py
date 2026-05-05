from PySide6.QtWidgets import QWidget, QVBoxLayout, QFileDialog

from nodan.coordinator.coordinator import Coordinator
from nodan.ui.canvas import Canvas
from nodan.ui.node import UINode


class EditorTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.canvas = Canvas()
        self.coordinator = Coordinator(self.canvas)
        self.canvas.coordinator = self.coordinator #TODO: Sort this out

        self.file_path: str | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)

    #region FILE HANDLING
    def new_file(self) -> None:
        self.coordinator.clear()
        self.file_path = None

    def save_file(self) -> None:
        if self.file_path is None:
            self.save_file_as()
            return

        self.coordinator.save_to_file(self.file_path)

    def save_file_as(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Graph",
            "",
            "NoDAn Graph (*.json);;JSON Files (*.json);;All Files (*)",
        )
        if not path:
            return

        self.coordinator.save_to_file(path)
        self.file_path = path

    def load_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Graph",
            "",
            "NoDAn Graph (*.json);;JSON Files (*.json);;All Files (*)",
        )
        if not path:
            return

        self.coordinator.load_from_file(path)
        self.file_path = path
    #endregion

    #region SUBGRAPHS
    def get_selected_nodes(self):
        selection = self.canvas.scene().selectedItems()
        if not selection:
            return

        selected_nodes = [
            item for item in selection
            if isinstance(item, UINode)
        ]

        return selected_nodes
    #endregion