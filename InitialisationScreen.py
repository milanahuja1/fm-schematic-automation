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
        self.loadSaveFileButton.clicked.connect(self.loadSaveFile)
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
        self.appManager.launchConfigureFiles(self.files)


    def check_ready(self):
        # Enable Create Graph if at least one file has been imported
        if len(self.files) > 0:
            self.createGraphButton.setEnabled(True)

    def loadSaveFile(self):
        self.appManager.load_state()
