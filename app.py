import sys
from PyQt6.QtWidgets import QApplication, QMainWindow
from mainwindow.MainWindow import MainWindow
from NetworkGenerator import NetworkGenerator
import os

class AppManager:
    nodePath = None
    pipePath = None
    monitorsPath = None
    userControlPath = None
    flumePath = None
    flapValvePath = None
    orificePath = None
    pumpPath = None
    sluicePath = None
    weirPath = None


    def createGraph(self):
        nodes = NetworkGenerator.loadNodes(appManager.nodePath)
        monitors = NetworkGenerator.loadMonitors(appManager.monitorsPath)

        #load in conduits:
        links = NetworkGenerator.loadEdges(appManager.pipePath)
        userControls = NetworkGenerator.loadEdges(appManager.userControlPath)
        flumes = NetworkGenerator.loadEdges(appManager.flumePath)
        flapValves = NetworkGenerator.loadEdges(appManager.flapValvePath)
        orfices = NetworkGenerator.loadEdges(appManager.orificePath)
        pumps = NetworkGenerator.loadEdges(appManager.pumpPath)
        sluices = NetworkGenerator.loadEdges(appManager.sluicePath)
        weirs = NetworkGenerator.loadEdges(appManager.weirPath)

        conduits = NetworkGenerator.generateConduits(links,userControls,flumes,flapValves,orfices,pumps,sluices,weirs)

        window.drawGraph(conduits, nodes, monitors, compressed=True)


appManager = AppManager()
app = QApplication(sys.argv)

#Instantiates a window
window = MainWindow(appManager)
window.show()
sys.exit(app.exec())