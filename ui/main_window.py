from PySide6.QtWidgets import QMainWindow

from coordinator.coordinator import Coordinator
from ui.canvas import Canvas


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("NoDAn")
        self.resize(1400, 860)

        self.canvas = Canvas()
        self.coordinator = Coordinator(self.canvas)
        self.canvas.coordinator = self.coordinator

        self._build_menu_bar()
        self.setCentralWidget(self.canvas)

    def _build_menu_bar(self) -> None:
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("File")

        self.new_action = file_menu.addAction("New...")
        self.open_action = file_menu.addAction("Open...")
        file_menu.addSeparator()
        self.save_action = file_menu.addAction("Save")
        self.save_as_action = file_menu.addAction("Save as...")
