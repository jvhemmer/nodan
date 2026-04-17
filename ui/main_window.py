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

        self.setCentralWidget(self.canvas)