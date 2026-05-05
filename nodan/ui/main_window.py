from PySide6.QtWidgets import QFileDialog, QMainWindow, QTabWidget

from nodan.coordinator.coordinator import Coordinator
from nodan.core.editor_tab import EditorTab
from nodan.ui.canvas import Canvas
from nodan.ui.node import UINode
from nodan.ui.subgraph_editor import SubgraphEditor


# TODO: Add tabs

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("NoDAn")
        self.resize(1400, 860)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.new_tab()
        self._build_menu_bar()

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
        tab = self.current_tab()
        if not tab:
            return
        tab.new_file()

    def _open_file(self) -> None:
        tab = self.current_tab()
        if not tab:
            return

        tab.load_file()

    def _save_file(self) -> None:
        tab = self.current_tab()
        if not tab:
            return
        tab.save_file()

    def _save_file_as(self) -> None:
        tab = self.current_tab()
        if not tab:
            return
        tab.save_file_as()

    # === Tabs ===
    def current_tab(self) -> EditorTab | None:
        widget = self.tabs.currentWidget()
        return widget if isinstance(widget, EditorTab) else None

    def new_tab(self) -> None:
        tab = EditorTab()
        self.tabs.addTab(tab, "Untitled")
        self.tabs.setCurrentWidget(tab)
