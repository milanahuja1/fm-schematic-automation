from PyQt6 import uic
from PyQt6.QtWidgets import QWidget, QFileDialog, QTableWidget, QTableWidgetItem, QLineEdit, QComboBox, QHeaderView
from PyQt6.QtCore import Qt
import os
import sys


class ConfigureFilesScreen(QWidget):
    def __init__(self, appManager, files):
        super().__init__()
        uic.loadUi("ConfigureFilesScreen.ui", self)

        self.appManager = appManager
        self.files = files
        self.initialiseUI()

    def initialiseUI(self):
        self.setWindowTitle("Configure Monitors")

        # Buttons
        if hasattr(self, "okButton"):
            self.okButton.clicked.connect(self.okButtonClicked)
            self.okButton.setEnabled(False)

        if hasattr(self, "closeButton"):
            self.closeButton.clicked.connect(self.backButtonClicked)




    def _updateOkEnabled(self):
        """Enable OK only when every row's Link dropdown has a selected link (not 'None')."""
        if not hasattr(self, "okButton"):
            return

        all_selected = True

        for row in range(self.table.rowCount()):
            link_widget = self.table.cellWidget(row, 2)
            if not isinstance(link_widget, QComboBox):
                all_selected = False
                break

            data = link_widget.currentData()
            # We store None for the "None" option
            if data is None:
                all_selected = False
                break

        self.okButton.setEnabled(all_selected)

    def okButtonClicked(self):
        monitorInformation = self._collectTableData()

        # Store on appManager for later use (safe default)
        self.appManager.completeMonitorConfig(monitorInformation)

    def backButtonClicked(self):
        self.appManager.launchInitialisationScreen()

