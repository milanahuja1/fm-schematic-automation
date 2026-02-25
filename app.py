import sys
from PyQt6.QtWidgets import QApplication, QMainWindow
from mainwindow.MainWindow import MainWindow
from NetworkGenerator import NetworkGenerator
import os

class AppManager:
    window = None

    def setWindow(self, window):
        self.window = window

    def launchConfigureMonitors(self):
        window.configureMonitors(self.monitors,self.links)

    def launchInitialisationScreen(self):
        self.window.initialiseParameters()

    def launchConfigureFiles(self, files):
        self.window.configureFiles(files)

    def completeFileConfig(self, fileConfigurationTable):
        #nodes
        self.nodesPath = fileConfigurationTable["nodes"]["path"]
        self.monitorsPath = fileConfigurationTable["monitors"]["path"]

        self.nodes = NetworkGenerator.loadNodes(self.nodesPath)
        self.monitors = NetworkGenerator.loadMonitors(self.monitorsPath)
        self.links = NetworkGenerator.generateLinks(fileConfigurationTable)
        self.launchConfigureMonitors()



    def completeMonitorConfig(self,monitorInformation):
        """
        monitorInformation[manhole_name] = {
                "monitorName": monitor_name,
                "note": note_text,
                "link": link_value}
        """
        self.monitorInformation = monitorInformation
        window.drawGraph(self.links, self.nodes, self.monitors, self.monitorInformation, compressed=True)
appManager = AppManager()
app = QApplication(sys.argv)

#Instantiates a window
window = MainWindow(appManager)
appManager.setWindow(window)
window.show()
sys.exit(app.exec())