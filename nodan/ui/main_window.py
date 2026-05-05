from PySide6.QtCore import Qt
from PySide6.QtGui import Qt
from PySide6.QtWidgets import QFileDialog, QMainWindow, QTabWidget, QWidget, QApplication, QPushButton

from nodan.core.editor_tab import EditorTab


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self._pending_plus_open = False

        self.setWindowTitle("NoDAn")
        self.resize(1400, 860)

        self.tabs = QTabWidget()
        self.tabs.tabBarClicked.connect(self.handle_tab_clicked)
        self.tabs.currentChanged.connect(self.handle_tab_changed)
        self.tabs.tabBarDoubleClicked.connect(self.handle_tab_doubleclicked)
        self.setCentralWidget(self.tabs)

        self.add_editor_tab()
        self.add_plus_tab()
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

        self.subgraph_new_action = subgraph_menu.addAction("New from selection...")
        self.subgraph_new_from_file_action = subgraph_menu.addAction("New from file...")
        self.subgraph_add_action = subgraph_menu.addAction("Add...")
        #TODO: Show all loaded subgraphs as a submenu of "Add..."

        self.subgraph_new_from_file_action.triggered.connect()

    ##region FILE MENU ACTIONS
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
    #endregion

    #region TABS
    def current_tab(self) -> EditorTab | None:
        widget = self.tabs.currentWidget()
        return widget if isinstance(widget, EditorTab) else None

    def add_editor_tab(self, name: str = "Untitled") -> None:
        tab = EditorTab()
        plus_idx = self.tabs.count() - 1
        self.tabs.insertTab(plus_idx, tab, name)
        self.tabs.setCurrentWidget(tab)

    def add_plus_tab(self):
        plus = QWidget()
        self.tabs.addTab(plus, "+")

    def handle_tab_clicked(self, index: int) -> None:
        plus_index = self.tabs.count() - 1
        self._pending_plus_open = index == plus_index

    def handle_tab_doubleclicked(self, index: int) -> None:
        plus_index = self.tabs.count() - 1

        if index < 0 or index == plus_index:
            return

        self._pending_plus_open = False

        self.tabs.setCurrentIndex(index-1)
        widget = self.tabs.widget(index)
        self.tabs.removeTab(index)
        if widget is not None:
            widget.deleteLater()

    #TODO: Add a timer to prevent double click unintentionally deleting tabs after creating a new one
    def handle_tab_changed(self, index: int) -> None:
        plus_index = self.tabs.count() - 1

        if not self._pending_plus_open:
            return

        if index != plus_index:
            self._pending_plus_open = False
            return

        self._pending_plus_open = False
        self.add_editor_tab()
    #endregion

    #region SUBGRAPHS
    def new_subgraph_from_file(self) -> None:
        tab = self.current_tab()

    def new_subgraph_from_selection(self):
        tab = self.current_tab()
        if not tab:
            return


    #endregion