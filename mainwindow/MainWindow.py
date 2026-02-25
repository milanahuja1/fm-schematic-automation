from PyQt6.QtWidgets import QGraphicsScene, QGraphicsView, QMainWindow
from SvgNodeFactory import SvgNodeFactory
from NetworkDrawer import NetworkDrawer
from InitialisationScreen import InitialisationScreen
from ConfigureMonitorsScreen import ConfigureMonitorsScreen
from ConfigureFilesScreen import ConfigureFilesScreen

class MainWindow(QMainWindow):
    def __init__(self, appManager):
        super().__init__()
        self.setWindowTitle("fm-schematic-automation")
        self.resize(1000, 700)
        self.appManager = appManager
        self.initialiseParameters()

    def drawGraph(self, conduits, nodes, monitors, monitorInformation, compressed=False):
        view = NetworkDrawer.drawNetwork(conduits, nodes, monitors, monitorInformation, compressed=compressed)
        self.setCentralWidget(view)

    def initialiseParameters(self):
        self.setCentralWidget(InitialisationScreen(self.appManager))

    def configureMonitors(self, monitors,links):
        self.setCentralWidget(ConfigureMonitorsScreen(self.appManager,monitors,links))

    def configureFiles(self, files):
        self.setCentralWidget(ConfigureFilesScreen(self.appManager,files))
