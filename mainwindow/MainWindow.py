from PyQt6.QtWidgets import QGraphicsScene, QGraphicsView, QMainWindow
from SvgNodeFactory import SvgNodeFactory
from NetworkDrawer import NetworkDrawer

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("fm-schematic-automation")
        self.resize(1000, 700)

    def drawGraph(self, graph, nodes):
        view = NetworkDrawer.drawNetwork(graph, nodes)
        self.setCentralWidget(view)
