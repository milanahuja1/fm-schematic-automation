from PyQt6 import uic
from PyQt6.QtWidgets import QWidget, QFileDialog, QTableWidget, QTableWidgetItem, QLineEdit, QComboBox, QHeaderView
from PyQt6.QtCore import Qt
import os
import sys


class ConfigureMonitorsScreen(QWidget):
    def __init__(self, appManager, monitors, links):
        super().__init__()
        uic.loadUi("ConfigureMonitorsScreen.ui", self)

        self.appManager = appManager
        self.monitors = monitors
        self.links = links
        self.linksByNode = self._buildLinksByNode(self.links)
        self.initialiseUI()

    def initialiseUI(self):
        self.setWindowTitle("Configure Monitors")

        # Buttons
        if hasattr(self, "okButton"):
            self.okButton.clicked.connect(self.okButtonClicked)
            self.okButton.setEnabled(False)

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

    def _normaliseNodeID(self, node_id):
        if node_id is None:
            return ""
        return str(node_id).strip()

    def _buildLinksByNode(self, links):
        """Build {node_id: [ {"id": str, "type": str}, ... ]} from a links list.

        Expected links format (list of dicts):
            {"id": str, "upstream": str, "downstream": str, "type": str}
        """
        by_node = {}
        if not links:
            return by_node

        for l in links:
            if not isinstance(l, dict):
                continue

            lid = self._normaliseNodeID(l.get("id"))
            up = self._normaliseNodeID(l.get("upstream"))
            ds = self._normaliseNodeID(l.get("downstream"))
            ltype = str(l.get("type", "link")).strip()

            if not lid:
                continue

            record = {"id": lid, "type": ltype}

            if up:
                by_node.setdefault(up, []).append(record)
            if ds:
                by_node.setdefault(ds, []).append(record)

        # De-duplicate per node by link id (keep first type seen)
        for node, records in list(by_node.items()):
            seen = set()
            deduped = []
            for r in records:
                rid = r.get("id")
                if rid in seen:
                    continue
                seen.add(rid)
                deduped.append(r)
            by_node[node] = deduped

        return by_node

    def _linkDisplayText(self, link_id, link_type):
        """e.g. TA047... .03 (weir)"""
        lt = str(link_type).strip()
        if lt == "":
            lt = "link"
        return f"{link_id} ({lt})"

    def _populateLinkDropdown(self, combo: QComboBox, node_id: str):
        combo.clear()

        # Always include a blank option
        combo.addItem("None", None)

        records = self.linksByNode.get(self._normaliseNodeID(node_id), [])
        for r in records:
            lid = r.get("id")
            ltype = r.get("type", "link")
            if not lid:
                continue
            combo.addItem(self._linkDisplayText(lid, ltype), {"id": lid, "type": ltype})

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

            # Col 2: link dropdown (QComboBox) populated per node
            combo = QComboBox(self.table)
            self._populateLinkDropdown(combo, manhole_name)
            combo.currentIndexChanged.connect(self._updateOkEnabled)
            self.table.setCellWidget(row, 2, combo)

            # Col 3: user text input (QLineEdit)
            note = QLineEdit(self.table)
            note.setPlaceholderText("Enter note…")
            self.table.setCellWidget(row, 3, note)

        self._updateOkEnabled()

    def _collectTableData(self):
        """Collect the edited values into a dict keyed by manhole name."""
        monitorInformation = {}
        for row in range(self.table.rowCount()):
            mh_item = self.table.item(row, 0)
            if mh_item is None:
                continue
            manhole_name = mh_item.text()

            monitor_widget = self.table.cellWidget(row, 1)
            monitor_name = monitor_widget.text() if isinstance(monitor_widget, QLineEdit) else ""

            link_widget = self.table.cellWidget(row, 2)
            link_value = ""
            if isinstance(link_widget, QComboBox):
                data = link_widget.currentData()
                if isinstance(data, dict) and data.get("id"):
                    link_value = data.get("id")
                else:
                    # None selected
                    link_value = ""

            note_widget = self.table.cellWidget(row, 3)
            note_text = note_widget.text() if isinstance(note_widget, QLineEdit) else ""

            monitorInformation[manhole_name] = {
                "monitorName": monitor_name,
                "note": note_text,
                "link": link_value,
            }

        return monitorInformation

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

    def closeButtonClicked(self):
        return
