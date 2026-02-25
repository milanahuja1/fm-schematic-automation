from PyQt6.QtWidgets import QGraphicsScene, QGraphicsView, QMainWindow, QFileDialog
from PyQt6.QtGui import QAction, QKeySequence
from SvgNodeFactory import SvgNodeFactory
from NetworkDrawer import NetworkDrawer
from InitialisationScreen import InitialisationScreen
from ConfigureMonitorsScreen import ConfigureMonitorsScreen
from ConfigureFilesScreen import ConfigureFilesScreen
from PyQt6.QtWidgets import QGraphicsView
from PyQt6.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self, appManager):
        super().__init__()
        self.setWindowTitle("fm-schematic-automation")
        self.resize(1000, 700)
        self.appManager = appManager
        self.initialiseParameters()
        self._createMenuBar()

    def _createMenuBar(self):
        file_menu = self.menuBar().addMenu("File")

        save_action = QAction("Save", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self._handleSave)

        file_menu.addAction(save_action)

    def _handleSave(self):
        # Call AppManager save_state (will open folder picker if needed)
        self.appManager.save_state()

    def drawGraph(self, conduits, nodes, monitors, monitorInformation, compressed=False):
        view = NetworkDrawer.drawNetwork(conduits, nodes, monitors, monitorInformation, compressed=compressed)
        # Enable drag-to-select multiple items
        view.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        view.setRubberBandSelectionMode(Qt.ItemSelectionMode.IntersectsItemShape)

        self.setCentralWidget(view)


    def initialiseParameters(self):
        self.setCentralWidget(InitialisationScreen(self.appManager))

    def configureMonitors(self, monitors,links):
        self.setCentralWidget(ConfigureMonitorsScreen(self.appManager,monitors,links))

    def configureFiles(self, files):
        self.setCentralWidget(ConfigureFilesScreen(self.appManager,files))
