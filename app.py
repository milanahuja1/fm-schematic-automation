import sys
from PyQt6.QtWidgets import QApplication, QMainWindow
from mainwindow.MainWindow import MainWindow
from NetworkGenerator import NetworkGenerator
import os

class AppManager:
    nodePath = None
    pipePath = None
    monitorsPath = None

    def createGraph(self):
        graph = NetworkGenerator.loadEdges(appManager.pipePath)
        nodes = NetworkGenerator.loadNodes(appManager.nodePath)
        monitors = NetworkGenerator.loadMonitors(appManager.monitorsPath)
        window.drawGraph(graph, nodes, monitors)


appManager = AppManager()
app = QApplication(sys.argv)

#Instantiates a window
window = MainWindow(appManager)
window.show()
sys.exit(app.exec())