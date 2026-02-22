import sys
from PyQt6.QtWidgets import QApplication, QMainWindow
from mainwindow.MainWindow import MainWindow
from NetworkGenerator import NetworkGenerator
import os

class AppManager:
    nodePath = None
    pipePath = None
    sensorsPath = None

    def createGraph(self):
        graph = NetworkGenerator.load_edges(appManager.pipePath)
        nodes = NetworkGenerator.load_nodes_with_xy(appManager.nodePath)
        window.drawGraph(graph, nodes)


appManager = AppManager()
app = QApplication(sys.argv)

#Instantiates a window
window = MainWindow(appManager)
window.show()
sys.exit(app.exec())