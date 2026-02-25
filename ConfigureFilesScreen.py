from PyQt6 import uic
from PyQt6.QtWidgets import QWidget, QFileDialog, QTableWidget, QTableWidgetItem, QLineEdit, QComboBox, QHeaderView
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPixmap, QIcon
import os
import sys


class ConfigureFilesScreen(QWidget):
    def __init__(self, appManager, files):
        super().__init__()
        uic.loadUi("ConfigureFilesScreen.ui", self)

        self.appManager = appManager
        self.files = files
        self.initialiseUI()

    def _makeColourIcon(self, hex_code: str, size: int = 14) -> QIcon:
        pix = QPixmap(size, size)
        pix.fill(QColor(hex_code))
        return QIcon(pix)

    def initialiseUI(self):
        self.setWindowTitle("Configure Files")

        # Buttons
        if hasattr(self, "okButton"):
            self.okButton.clicked.connect(self.okButtonClicked)
            self.okButton.setEnabled(False)

        if hasattr(self, "closeButton"):
            self.closeButton.clicked.connect(self.backButtonClicked)

        # Populate fileConfigTable with filenames in leftmost column and two dropdown columns
        if hasattr(self, "fileConfigTable"):
            # Table columns: Filename + two dropdown configuration columns
            self.fileConfigTable.setColumnCount(3)
            self.fileConfigTable.setHorizontalHeaderLabels([
                "Filename",
                "File type",
                "Colour",
            ])

            # Dropdown options (edit these to match your app)
            file_type_options = [
                ("Select…", None),
                ("Weirs", "weirs"),
                ("Flumes", "flumes"),
                ("Nodes", "nodes"),
                ("Monitors", "monitors"),
                ("Orifices", "orifices"),
                ("Pumps", "pumps"),
                ("Conduits", "conduits"),
                ("Sluices", "sluices"),
                ("User controls", "user_controls"),
                ("Flap valves", "flap_valves"),
            ]

            self.fileConfigTable.setRowCount(len(self.files))

            for row, filepath in enumerate(self.files):
                filename = os.path.basename(filepath)

                # Col 0: filename (read-only)
                item = QTableWidgetItem(filename)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.fileConfigTable.setItem(row, 0, item)

                # Col 1: file type dropdown
                type_combo = QComboBox(self.fileConfigTable)
                for label, value in file_type_options:
                    type_combo.addItem(label, value)
                type_combo.currentIndexChanged.connect(self._updateOkEnabled)
                type_combo.currentIndexChanged.connect(
                    lambda _, r=row: self._updateColourEnabled(r)
                )
                self.fileConfigTable.setCellWidget(row, 1, type_combo)

                # Col 2: colour dropdown
                colour_combo = QComboBox(self.fileConfigTable)

                colours = [
                    ("Red", "#e74c3c"),
                    ("Blue", "#3498db"),
                    ("Green", "#2ecc71"),
                    ("Orange", "#e67e22"),
                    ("Purple", "#9b59b6"),
                    ("Teal", "#1abc9c"),
                    ("Yellow", "#f1c40f"),
                    ("Pink", "#ff69b4"),
                    ("Brown", "#8e5a2b"),
                    ("Grey", "#7f8c8d"),
                ]

                for name, hex_code in colours:
                    # Store hex code as the item's data, and show a coloured swatch icon
                    colour_combo.addItem(self._makeColourIcon(hex_code), name, hex_code)

                colour_combo.currentIndexChanged.connect(self._updateOkEnabled)

                # Distribute default colours across rows
                if colour_combo.count() > 0:
                    colour_combo.setCurrentIndex(row % colour_combo.count())

                self.fileConfigTable.setCellWidget(row, 2, colour_combo)
                self._updateColourEnabled(row)

            header = self.fileConfigTable.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)

            # Set initial OK enabled state
            self._updateOkEnabled()

    def _updateColourEnabled(self, row: int):
        """Disable colour dropdown for Nodes and Monitors file types."""
        if not hasattr(self, "fileConfigTable"):
            return

        table = self.fileConfigTable

        type_widget = table.cellWidget(row, 1)
        colour_widget = table.cellWidget(row, 2)

        if not isinstance(type_widget, QComboBox) or not isinstance(colour_widget, QComboBox):
            return

        selected_type = type_widget.currentData()

        # Disable colour for nodes and monitors
        if selected_type in ("nodes", "monitors"):
            colour_widget.setEnabled(False)
        else:
            colour_widget.setEnabled(True)

    def _updateOkEnabled(self):
        """Enable OK only when every row has selections for both dropdown columns."""
        if not hasattr(self, "okButton"):
            return
        if not hasattr(self, "fileConfigTable"):
            self.okButton.setEnabled(False)
            return

        table = self.fileConfigTable
        all_selected = True

        for row in range(table.rowCount()):
            type_widget = table.cellWidget(row, 1)
            import_widget = table.cellWidget(row, 2)

            if not isinstance(type_widget, QComboBox) or not isinstance(import_widget, QComboBox):
                all_selected = False
                break

            if type_widget.currentData() is None:
                all_selected = False
                break

        self.okButton.setEnabled(all_selected)


    def _collectTableData(self):
        """
        Collect configuration from fileConfigTable.

        Returns:
            dict mapping filename -> {
                "type": selected file type (str),
                "colour": selected colour hex (str or None)
            }
        """
        config = {}

        if not hasattr(self, "fileConfigTable"):
            return config

        table = self.fileConfigTable

        for row in range(table.rowCount()):
            filename_item = table.item(row, 0)
            type_widget = table.cellWidget(row, 1)
            colour_widget = table.cellWidget(row, 2)

            if filename_item is None:
                continue

            filename = filename_item.text()

            file_type = None
            if isinstance(type_widget, QComboBox):
                file_type = type_widget.currentData()

            colour = None
            if isinstance(colour_widget, QComboBox) and colour_widget.isEnabled():
                colour = colour_widget.currentData()

            config[filename] = {
                "type": file_type,
                "colour": colour,
            }

        return config

    def okButtonClicked(self):
        fileConfiguration = self._collectTableData()

        # Debug print
        print("[DEBUG] File configuration:", fileConfiguration)

        # Store on appManager for later use
        if hasattr(self.appManager, "completeFileConfig"):
            self.appManager.completeFileConfig(fileConfiguration)

        # Return to previous screen or continue flow
        self.appManager.launchInitialisationScreen()

    def backButtonClicked(self):
        self.appManager.launchInitialisationScreen()
