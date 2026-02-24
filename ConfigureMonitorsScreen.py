from PyQt6 import uic
from PyQt6.QtWidgets import QWidget, QFileDialog, QTableWidget, QTableWidgetItem, QLineEdit, QComboBox, QHeaderView
from PyQt6.QtCore import Qt
import os
import sys


class ConfigureMonitorsScreen(QWidget):
    def __init__(self, appManager, monitors,links):
        super().__init__()
        uic.loadUi("ConfigureMonitorsScreen.ui", self)

        self.appManager = appManager
        self.monitors = monitors

        # Link dropdown options
        self.linkOptions = [
            "None",
            "Upstream",
            "Downstream",
        ]

        self.initialiseUI()

    def initialiseUI(self):
        self.setWindowTitle("Configure Monitors")

        # Buttons
        if hasattr(self, "okButton"):
            self.okButton.clicked.connect(self.okButtonClicked)
        if hasattr(self, "closeButton"):
            self.closeButton.clicked.connect(self.closeButtonClicked)

        # Table
        self._setupTable()
        self._populateTable()

    def _setupTable(self):
        """Create/find the table widget and configure headings."""
        # Table is defined in the .ui as 'monitorConfigTable'
        self.table = self.monitorConfigTable

        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            "Manhole name",
            "Monitor name",
            "Link",
            "Notes (optional)",
        ])

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)

        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

    def _normaliseMonitors(self):
        """Return a list of (manhole_name, monitor_name) pairs from whatever input we get."""
        monitors = self.monitors
        if monitors is None:
            return []

        # dict: {manhole: monitor}
        if isinstance(monitors, dict):
            out = []
            for k, v in monitors.items():
                out.append((str(k), "" if v is None else str(v)))
            return out

        # list/tuple: could be ["MH1", "MH2"] or [("MH1","MON1"), ...]
        out = []
        try:
            for item in monitors:
                if isinstance(item, (list, tuple)) and len(item) >= 2:
                    out.append((str(item[0]), "" if item[1] is None else str(item[1])))
                else:
                    out.append((str(item), ""))
        except TypeError:
            return []

        return out

    def _populateTable(self):
        """Populate rows from the monitors/manholes list."""
        pairs = self._normaliseMonitors()
        self.table.setRowCount(len(pairs))

        for row, (manhole_name, monitor_name) in enumerate(pairs):
            # Col 0: manholeName (read-only item)
            mh_item = QTableWidgetItem(manhole_name)
            mh_item.setFlags(mh_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 0, mh_item)

            # Col 1: monitorName (user editable QLineEdit)
            monitor_edit = QLineEdit(self.table)
            monitor_edit.setPlaceholderText("Enter monitor name…")
            self.table.setCellWidget(row, 1, monitor_edit)

            # Col 2: link dropdown (QComboBox)
            combo = QComboBox(self.table)
            combo.addItems(self.linkOptions)
            self.table.setCellWidget(row, 2, combo)

            # Col 3: user text input (QLineEdit)
            note = QLineEdit(self.table)
            note.setPlaceholderText("Enter note…")
            self.table.setCellWidget(row, 3, note)

    def _collectTableData(self):
        """Collect the edited values into a dict keyed by manhole name."""
        result = {}
        for row in range(self.table.rowCount()):
            mh_item = self.table.item(row, 0)
            if mh_item is None:
                continue
            manhole_name = mh_item.text()

            monitor_widget = self.table.cellWidget(row, 1)
            monitor_name = monitor_widget.text() if isinstance(monitor_widget, QLineEdit) else ""

            link_widget = self.table.cellWidget(row, 2)
            link_value = link_widget.currentText() if isinstance(link_widget, QComboBox) else ""

            note_widget = self.table.cellWidget(row, 3)
            note_text = note_widget.text() if isinstance(note_widget, QLineEdit) else ""

            result[manhole_name] = {
                "monitorName": monitor_name,
                "note": note_text,
                "link": link_value,
            }

        return result

    def okButtonClicked(self):
        data = self._collectTableData()

        # Store on appManager for later use (safe default)
        self.appManager.monitorConfig = data

        self.close()

    def closeButtonClicked(self):
        self.close()
