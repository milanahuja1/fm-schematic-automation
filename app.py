import sys
from PyQt6.QtWidgets import QApplication, QMainWindow
from mainwindow.MainWindow import MainWindow
from NetworkGenerator import NetworkGenerator
import os

class AppManager:
    nodePath = None
    conduitPath = None
    monitorsPath = None
    userControlPath = None
    flumePath = None
    flapValvePath = None
    orificePath = None
    pumpPath = None
    sluicePath = None
    weirPath = None


    def createGraph(self):
        self.loadData()
        self.links = NetworkGenerator.generateLinks(self.conduits, self.userControls, self.flumes, self.flapValves, self.orfices, self.pumps, self.sluices, self.weirs)
        window.configureMonitors(self.monitors,self.links)


    def completeMonitorConfig(self,monitorInformation):
        """
        monitorInformation[manhole_name] = {
                "monitorName": monitor_name,
                "note": note_text,
                "link": link_value}
        """
        self.monitorInformation = monitorInformation
        window.drawGraph(self.links, self.nodes, self.monitors, compressed=True)

    def loadData(self):
        self.nodes = NetworkGenerator.loadNodes(appManager.nodePath)
        self.monitors = NetworkGenerator.loadMonitors(appManager.monitorsPath)

        #links:
        self.conduits = NetworkGenerator.loadEdges(self.conduitPath)
        self.userControls = NetworkGenerator.loadEdges(self.userControlPath)
        self.flumes = NetworkGenerator.loadEdges(self.flumePath)
        self.flapValves = NetworkGenerator.loadEdges(self.flapValvePath)
        self.orfices = NetworkGenerator.loadEdges(self.orificePath)
        self.pumps = NetworkGenerator.loadEdges(self.pumpPath)
        self.sluices = NetworkGenerator.loadEdges(self.sluicePath)
        self.weirs = NetworkGenerator.loadEdges(self.weirPath)
appManager = AppManager()
app = QApplication(sys.argv)

#Instantiates a window
window = MainWindow(appManager)
window.show()
sys.exit(app.exec())