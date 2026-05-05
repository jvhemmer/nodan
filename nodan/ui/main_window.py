from PySide6.QtWidgets import QFileDialog, QMainWindow

from nodan.coordinator.coordinator import Coordinator
from nodan.ui.canvas import Canvas
from nodan.ui.node import UINode
from nodan.ui.subgraph_editor import SubgraphEditor


# TODO: Add tabs

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("NoDAn")
        self.resize(1400, 860)

        self.canvas = Canvas()
        self.coordinator = Coordinator(self.canvas)
        self.canvas.coordinator = self.coordinator
        self._current_file_path: str | None = None

        self.subgraph_editor: SubgraphEditor | None = None

        self._build_menu_bar()
        self.setCentralWidget(self.canvas)

    def _build_menu_bar(self) -> None:
        menu_bar = self.menuBar()

        # File menu
        file_menu = menu_bar.addMenu("File")

        self.new_action = file_menu.addAction("New")
        self.open_action = file_menu.addAction("Open...")
        file_menu.addSeparator()
        self.save_action = file_menu.addAction("Save")
        self.save_as_action = file_menu.addAction("Save as...")

        self.new_action.triggered.connect(self._new_file)
        self.open_action.triggered.connect(self._open_file)
        self.save_action.triggered.connect(self._save_file)
        self.save_as_action.triggered.connect(self._save_file_as)

        # Subgraph menu
        subgraph_menu = menu_bar.addMenu("Subgraph")

        self.subgraph_new_action = subgraph_menu.addAction("New from selection")
        self.subgraph_add_action = subgraph_menu.addAction("Add...")
        #TODO: Show all loaded subgraphs as a submenu of "Add..."

    # === File Menu actions ===
    def _new_file(self) -> None:
        self.coordinator.clear()
        self._current_file_path = None

    def _open_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Graph",
            "",
            "NoDAn Graph (*.json);;JSON Files (*.json);;All Files (*)",
        )
        if not path:
            return

        self.coordinator.load_from_file(path)
        self._current_file_path = path

    def _save_file(self) -> None:
        if self._current_file_path is None:
            self._save_file_as()
            return

        self.coordinator.save_to_file(self._current_file_path)

    def _save_file_as(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Graph",
            "",
            "NoDAn Graph (*.json);;JSON Files (*.json);;All Files (*)",
        )
        if not path:
            return

        self.coordinator.save_to_file(path)
        self._current_file_path = path

    # === Subgraph actions ===
    def new_subgraph_from_selection(self):
        selection = self.canvas.scene().selectedItems()
        if not selection:
            return

        nodes = [
            item for item in selection
            if isinstance(item, UINode)
        ]

        draft = self.canvas.coordinator.build_subgraph_definition(nodes, subgraph_id="new_subgraph", title="New Subgraph")

        self.subgraph_editor = SubgraphEditor(draft)
        self.subgraph_editor.show()
