import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QFileDialog
from mainwindow.MainWindow import MainWindow
from NetworkGenerator import NetworkGenerator
import pickle

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


    def save_state(self, path=None):
        """Save nodes/links/monitors/monitorInformation to a pickle file.

        If `path` is not provided, a folder picker is shown and the state is saved as
        `schematic_state.pkl` inside the chosen folder.
        """
        if not path:
            folder = QFileDialog.getExistingDirectory(
                self.window,
                "Choose a folder to save the state",
                "",
            )
            if not folder:
                return  # user cancelled

            path = os.path.join(folder, "schematic_state.pkl")

        payload = {
            "nodes": self.nodes,
            "links": self.links,
            "monitors": self.monitors,
            "monitorInformation": self.monitorInformation,
        }

        with open(path, "wb") as f:
            pickle.dump(payload, f, protocol=pickle.HIGHEST_PROTOCOL)

        print(f"[DEBUG] Saved state to: {path}")

    def load_state(self, path=None):
        """Load nodes/links/monitors/monitorInformation from a pickle file.

        If `path` is not provided, a file picker is shown.
        """
        if not path:
            path, _ = QFileDialog.getOpenFileName(
                self.window,
                "Select a saved schematic state",
                "",
                "Pickle files (*.pkl);;All files (*)",
            )
            if not path:
                return None  # user cancelled

        with open(path, "rb") as f:
            payload = pickle.load(f)

        print(f"[DEBUG] Loaded state from: {path}")


        self.nodes = payload.get("nodes")
        self.links =payload.get("links")
        self.monitors = payload.get("monitors")
        self.monitorInformation = payload.get("monitorInformation")
        window.drawGraph(self.links, self.nodes, self.monitors, self.monitorInformation, compressed=True)
appManager = AppManager()
app = QApplication(sys.argv)

#Instantiates a window
window = MainWindow(appManager)
appManager.setWindow(window)
window.show()
sys.exit(app.exec())