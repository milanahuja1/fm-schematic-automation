from PyQt6 import uic
from PyQt6.QtWidgets import QWidget, QFileDialog
import os
import sys

class ConfigureMonitorRow(QWidget):
    def __init__(self, appManager):
        super().__init__()
        uic.loadUi("ConfigureMonitorsScreen.ui", self)
        self.appManager = appManager

