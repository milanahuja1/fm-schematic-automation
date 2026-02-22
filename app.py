import sys
from PyQt6.QtWidgets import QApplication, QMainWindow
from mainwindow.MainWindow import MainWindow
from NetworkGenerator import NetworkGenerator
import os
import csv

app = QApplication(sys.argv)
#Instantiates a window
window = MainWindow()
window.show()

base_dir = os.path.dirname(os.path.abspath(__file__))
nodePath = os.path.join(base_dir, "data", "nodeTable.csv")
edgesPath = os.path.join(base_dir, "data", "edgeTable.csv")
sensorsPath = os.path.join(base_dir, "data", "sensors.csv")
sensors = NetworkGenerator.loadSensorData(sensorsPath)
graph = NetworkGenerator.load_edges(edgesPath)
nodes = NetworkGenerator.load_nodes_with_xy(nodePath)
sensorGraph, reducedNodes = NetworkGenerator.build_sensor_reduced_graph(graph,nodes, sensors)



window.drawGraph(sensorGraph, reducedNodes)

sys.exit(app.exec())