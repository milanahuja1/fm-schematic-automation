import sys
from PyQt6.QtWidgets import QApplication, QMainWindow
from mainwindow.MainWindow import MainWindow
from NetworkGenerator import NetworkGenerator
from PyQt6.QtGui import QFontDatabase
import os

class AppManager:
    nodePath = None
    pipePath = None
    sensorsPath = None

    def createGraph(self):
        graph = NetworkGenerator.load_edges(appManager.pipePath)
        nodes = NetworkGenerator.load_nodes_with_xy(appManager.nodePath)
        if self.sensorsPath is not None:
            sensors = NetworkGenerator.loadSensorData(appManager.sensorsPath)
            graph, nodes= NetworkGenerator.build_sensor_reduced_graph(graph, nodes,sensors)
        window.drawGraph(graph, nodes)


appManager = AppManager()
app = QApplication(sys.argv)

base_dir = os.path.dirname(os.path.abspath(__file__))
font_path = os.path.join(base_dir, "fonts", "FiraCode-Medium.ttf")
font_id = QFontDatabase.addApplicationFont(font_path)
print("font loaded:", font_id != -1)

#Instantiates a window
window = MainWindow(appManager)
window.show()
sys.exit(app.exec())