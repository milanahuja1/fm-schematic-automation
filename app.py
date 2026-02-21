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

graph = NetworkGenerator.load_edges(edgesPath)

def load_nodes_with_xy(filename):
    """
    Reads a node CSV with columns: id,type,x,y
    Returns:
        { node_id: {"type": int, "x": float, "y": float}, ... }
    """
    node_map = {}

    with open(filename, newline="") as f:
        reader = csv.DictReader(f)
        # Expecting: id,type,x,y
        for row in reader:
            node_id = row["id"]
            node_map[node_id] = {
                "type": int(row["type"]),
                "x": float(row["x"]),
                "y": float(row["y"]),
            }

    return node_map

nodes = load_nodes_with_xy(nodePath)
window.drawGraph(graph, nodes)

sys.exit(app.exec())