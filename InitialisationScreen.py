from PyQt6 import uic
from PyQt6.QtWidgets import QWidget, QFileDialog
import os
import sys


class InitialisationScreen(QWidget):
    def __init__(self, appManager):
        super().__init__()
        uic.loadUi("InitialisationScreen.ui", self)
        self.appManager = appManager

        # Enable drag and drop on the import frame
        self.importFrame.setAcceptDrops(True)
        # Forward drag/drop events from the frame to this widget
        self.importFrame.installEventFilter(self)

        #Grey out the createGraph button
        self.createGraphButton.setEnabled(False)


        # Connect import buttons
        self.useSampleDataButton.clicked.connect(self.useSampleData)
        self.createGraphButton.clicked.connect(self.loadData)

        self.files = []

    def eventFilter(self, obj, event):
        if obj == self.importFrame:
            if event.type() == event.Type.DragEnter:
                self.dragEnterEvent(event)
                return True
            if event.type() == event.Type.Drop:
                self.dropEvent(event)
                return True
            if event.type() == event.Type.MouseButtonPress:
                self.openFileDialog()
                return True
        return super().eventFilter(obj, event)

    def dragEnterEvent(self, event):
        # Accept only file drops
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if not urls:
            return

        csv_files = []
        for url in urls:
            file_path = url.toLocalFile()
            if file_path.lower().endswith(".csv"):
                csv_files.append(file_path)

        if not csv_files:
            return

        filenames = [os.path.basename(f) for f in csv_files]
        self.importLabel.setText("\n".join(filenames))
        self.files = csv_files
        self.check_ready()

    def openFileDialog(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select CSV Files",
            "",
            "CSV Files (*.csv);;All Files (*)"
        )

        if not files:
            return

        filenames = [os.path.basename(f) for f in files]
        self.importLabel.setText("\n".join(filenames))
        self.files = files
        self.check_ready()

    def loadData(self):
        self.appManager.launchConfigureMonitors()


    def check_ready(self):
        # Enable Create Graph if at least one file has been imported
        if len(self.files) > 0:
            self.createGraphButton.setEnabled(True)

    def useSampleData(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.appManager.nodePath = os.path.join(base_dir, "sampleData", "Muston_Nodes.csv")
        self.appManager.monitorsPath = os.path.join(base_dir, "sampleData", "Muston_Monitors.csv")
        #links:
        self.appManager.conduitPath = os.path.join(base_dir, "sampleData", "Muston_Links.csv")
        self.appManager.userControlPath = os.path.join(base_dir, "sampleData", "User_Control.csv")
        self.appManager.flumePath = os.path.join(base_dir, "sampleData", "Muston_flumes.csv")
        self.appManager.flapValvePath = os.path.join(base_dir, "sampleData", "Muston_Flap_Valve.csv")
        self.appManager.orificePath = os.path.join(base_dir, "sampleData", "Muston_Orifices.csv")
        self.appManager.pumpPath = os.path.join(base_dir, "sampleData", "Muston_Pumps.csv")
        self.appManager.sluicePath = os.path.join(base_dir, "sampleData", "Muston_Sluice.csv")
        self.appManager.weirPath = os.path.join(base_dir, "sampleData", "Muston_Weirs.csv")

        self.appManager.launchConfigureMonitors()