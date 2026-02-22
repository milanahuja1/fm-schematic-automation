from PyQt6 import uic
from PyQt6.QtWidgets import QWidget, QFileDialog
from PyQt6.QtGui import QFont
import os
import sys


class InitialisationScreen(QWidget):
    def __init__(self, appManager):
        super().__init__()
        uic.loadUi("InitialisationScreen.ui", self)
        self.appManager = appManager

        # Set custom button font
        button_font = QFont("Fira Code", 11)
        button_font.setBold(True)

        self.importNodesButton.setFont(button_font)
        self.importPipesButton.setFont(button_font)
        self.importSensorsButton.setFont(button_font)
        self.useSampleDataButton.setFont(button_font)
        self.createGraphButton.setFont(button_font)

        #Grey out the createGraph button
        self.createGraphButton.setEnabled(False)

        # Store selected file paths
        self.nodes_file = None
        self.pipes_file = None
        self.sensors_file = None

        # Connect import buttons
        self.importNodesButton.clicked.connect(self.import_nodes)
        self.importPipesButton.clicked.connect(self.import_pipes)
        self.importSensorsButton.clicked.connect(self.import_sensors)
        self.useSampleDataButton.clicked.connect(self.useSampleData)
        self.createGraphButton.clicked.connect(self.createGraph)

    def createGraph(self):
        self.appManager.createGraph()

    def useSampleData(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.appManager.pipePath = edgesPath = os.path.join(base_dir, "data", "edgeTable.csv")
        self.appManager.nodePath = os.path.join(base_dir, "data", "nodeTable.csv")
        self.appManager.sensorsPath = os.path.join(base_dir, "data", "sensors.csv")
        self.appManager.createGraph()


    def import_nodes(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Nodes CSV",
            "",
            "CSV Files (*.csv);;All Files (*)"
        )
        if file_path:
            self.nodes_file = file_path
            self.importNodesLabel.setText(file_path)
            self.appManager.nodePath = file_path
            self.check_ready()

    def import_pipes(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Pipes CSV",
            "",
            "CSV Files (*.csv);;All Files (*)"
        )
        if file_path:
            self.pipes_file = file_path
            self.importPipesLabel.setText(file_path)
            self.appManager.pipePath = file_path
            self.check_ready()

    def import_sensors(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Sensors CSV",
            "",
            "CSV Files (*.csv);;All Files (*)"
        )
        if file_path:
            self.sensors_file = file_path
            self.importSensorsLabel.setText(file_path)
            self.appManager.sensorsPath = file_path
            self.check_ready()

    def check_ready(self):
        if self.nodes_file and self.pipes_file:
            self.createGraphButton.setEnabled(True)
        else:
            self.createGraphButton.setEnabled(False)