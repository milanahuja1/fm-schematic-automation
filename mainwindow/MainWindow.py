from PyQt6.QtWidgets import QApplication, QMainWindow
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("fm-schematic-automation")
        self.resize(800, 600)
