from PyQt6 import uic
from PyQt6.QtWidgets import QWidget, QFileDialog
import os
import sys


class InitialisationScreen(QWidget):
    def __init__(self, appManager):
        super().__init__()
        uic.loadUi("InitialisationScreen.ui", self)
        self.appManager = appManager

        #Grey out the createGraph button
        self.createGraphButton.setEnabled(False)

        # Store selected file paths
        self.nodes_file = None
        self.pipes_file = None
        self.sensors_file = None

        # Connect import buttons
        self.importNodeButton.clicked.connect(self.importNodes)
        self.importMonitorButton.clicked.connect(self.importMonitors)
        self.useSampleDataButton.clicked.connect(self.useSampleData)
        self.createGraphButton.clicked.connect(self.createGraph)


        # Conduit import mapping (button name -> label + appManager path attribute)
        # Note: "links" are the base pipes network.
        self.conduitButtonMap = {
            "importLinkButton": {"label": "importLinkLabel", "path_attr": "pipePath", "title": "Select Links CSV"},
            "importUserControlButton": {"label": "importUserControlLabel", "path_attr": "userControlPath", "title": "Select User Control CSV"},
            "importFlumeButton": {"label": "importFlumeLabel", "path_attr": "flumePath", "title": "Select Flumes CSV"},
            "importFlapValveButton": {"label": "importFlapValveLabel", "path_attr": "flapValvePath", "title": "Select Flap Valves CSV"},
            "importOrificeButton": {"label": "importOrificeLabel", "path_attr": "orificePath", "title": "Select Orifices CSV"},
            "importPumpButton": {"label": "importPumpLabel", "path_attr": "pumpPath", "title": "Select Pumps CSV"},
            "importSluiceButton": {"label": "importSluiceLabel", "path_attr": "sluicePath", "title": "Select Sluices CSV"},
            "importWeirButton": {"label": "importWeirLabel", "path_attr": "weirPath", "title": "Select Weirs CSV"},
        }

        # Store selected conduit paths by type
        self.conduit_files = {}

        # Connect all conduit import buttons to one handler
        for button_name in self.conduitButtonMap:
            btn = getattr(self, button_name, None)
            if btn is not None:
                btn.clicked.connect(self.importConduit)

    def createGraph(self):
        self.appManager.createGraph()

    def useSampleData(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.appManager.nodePath = os.path.join(base_dir, "sampleData", "Muston_Nodes.csv")
        self.appManager.monitorsPath = os.path.join(base_dir, "sampleData", "Muston_Monitors.csv")
        #conduits:
        self.appManager.pipePath = os.path.join(base_dir, "sampleData", "Muston_Links.csv")
        self.appManager.userControlPath = os.path.join(base_dir, "sampleData", "User_Control.csv")
        self.appManager.flumePath = os.path.join(base_dir, "sampleData", "Muston_flumes.csv")
        self.appManager.flapValvePath = os.path.join(base_dir, "sampleData", "Muston_Flap_Valve.csv")
        self.appManager.orificePath = os.path.join(base_dir, "sampleData", "Muston_Orifices.csv")
        self.appManager.pumpPath = os.path.join(base_dir, "sampleData", "Muston_Pumps.csv")
        self.appManager.sluicePath = os.path.join(base_dir, "sampleData", "Muston_Sluice.csv")
        self.appManager.weirPath = os.path.join(base_dir, "sampleData", "Muston_Weirs.csv")


        self.appManager.createGraph()


    def importNodes(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Nodes CSV",
            "",
            "CSV Files (*.csv);;All Files (*)"
        )
        if file_path:
            self.nodes_file = file_path
            self.importNodeLabel.setText(file_path)
            self.appManager.nodePath = file_path
            self.check_ready()

    def importConduit(self):
        btn = self.sender()
        if btn is None:
            return

        button_name = btn.objectName()
        config = self.conduitButtonMap.get(button_name)
        if config is None:
            return

        title = config.get("title", "Select CSV")

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            title,
            "",
            "CSV Files (*.csv);;All Files (*)"
        )

        if not file_path:
            return

        # Update the matching label in the UI
        label_name = config.get("label")
        label_widget = getattr(self, label_name, None)
        if label_widget is not None:
            label_widget.setText(file_path)

        # Save onto appManager (e.g., appManager.pipePath, appManager.weirPath, ...)
        path_attr = config.get("path_attr")
        if path_attr:
            setattr(self.appManager, path_attr, file_path)

        # Track what the user selected
        self.conduit_files[button_name] = file_path

        # For readiness, treat links (base pipes) as the required "pipes_file"
        if button_name == "importLinkButton":
            self.pipes_file = file_path

        self.check_ready()

    def importMonitors(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Monitors CSV",
            "",
            "CSV Files (*.csv);;All Files (*)"
        )
        if file_path:
            self.sensors_file = file_path
            self.importMonitorLabel.setText(file_path)
            self.appManager.monitorsPath = file_path
            self.check_ready()

    def check_ready(self):
        if self.nodes_file and self.pipes_file:
            self.createGraphButton.setEnabled(True)
        else:
            self.createGraphButton.setEnabled(False)