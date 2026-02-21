from PyQt6.QtWidgets import QMainWindow
from NetworkDrawer import NetworkDrawer


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("fm-schematic-automation")
        self.resize(800, 600)

    def drawGraph(self, graph, nodes):
        view = NetworkDrawer.drawNetwork(graph, nodes)
        self.setCentralWidget(view)