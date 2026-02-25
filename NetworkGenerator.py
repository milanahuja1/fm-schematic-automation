import csv

class NetworkGenerator:


    @staticmethod
    def loadNodes(filename):
        """
        Reads a node CSV with columns:
            - Node ID
            - Node type
            - x (m)  (optional)
            - y (m)  (optional)

        Returns:
            { node_id: {"type": str, "x": float, "y": float}, ... }
        """
        nodeMap = {}

        # Use utf-8-sig to automatically strip BOM if present
        with open(filename, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)

            # Normalise headers (strip whitespace)
            if reader.fieldnames:
                reader.fieldnames = [name.strip() if name else name for name in reader.fieldnames]

            for row in reader:
                nodeID = row["Node ID"]
                nodeType = row["Node type"]

                # Optional coordinates
                x_raw = row.get("x (m)")
                y_raw = row.get("y (m)")

                def _to_float(val):
                    if val is None:
                        return 0.0
                    s = str(val).strip()
                    if s == "":
                        return 0.0
                    try:
                        return float(s)
                    except ValueError:
                        return 0.0

                nodeMap[nodeID] = {
                    "type": str(nodeType).strip(),
                    "x": _to_float(x_raw),
                    "y": _to_float(y_raw),
                }
        return nodeMap

    @staticmethod
    def loadMonitors(filename):
        """
        Reads a monitor CSV with columns: Node ID, Node type
        Returns:
            { node_id: {"type": str}, ... }
        """
        monitorMap = {}

        # Use utf-8-sig to automatically strip BOM if present
        with open(filename, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)

            # Normalise headers (strip whitespace)
            if reader.fieldnames:
                reader.fieldnames = [name.strip() if name else name for name in reader.fieldnames]

            for row in reader:
                nodeID = row["Node ID"]
                nodeType = row["Node type"]

                monitorMap[nodeID] = {
                    "type": str(nodeType).strip()
                }

        return monitorMap

    @staticmethod
    def loadEdges(filename):

        graph = {}
        # Allow optional conduit files: if no filename provided, return empty graph
        if filename is None or str(filename).strip() == "":
            return graph

        # Use utf-8-sig to automatically strip BOM if present
        with open(filename, newline="", encoding="utf-8-sig") as file:
            reader = csv.DictReader(file)
            # Normalise headers (strip whitespace)
            if reader.fieldnames:
                reader.fieldnames = [name.strip() if name else name for name in reader.fieldnames]

            for row in reader:
                upstream = row["US node ID"]
                suffix = row["Link suffix"]
                downstream = row["DS node ID"]
                link_id = f"{upstream}.{suffix}"
                if upstream not in graph:
                    graph[upstream] = []
                graph[upstream].append((downstream, link_id))
        return graph

    @staticmethod
    def generateLinks(fileConfigurationTable):
        """Build a unified list of all link objects from the configured CSV files.

        `fileConfigurationTable` is expected to look like:
            {
                "conduits": {"path": "/.../Conduits.csv", "colour": "#3498db"},
                "weirs": {"path": "/.../Weirs.csv", "colour": "#e74c3c"},
                "nodes": {"path": "/.../Nodes.csv", "colour": None},
                "monitors": {"path": "/.../Monitors.csv", "colour": None},
                ...
            }

        Returns:
            A list of dicts, one per link:
                {
                    "id": str,
                    "upstream": str,
                    "downstream": str,
                    "type": str,       # e.g. conduits/weirs/orifices
                    "colour": str|None # colour configured for this file type
                }
        """
        all_links = []
        seen_ids = set()

        if not fileConfigurationTable:
            return all_links

        for linkType, meta in fileConfigurationTable.items():
            # Skip non-link datasets
            if linkType in ("nodes", "monitors"):
                continue

            path = None
            colour = None
            if isinstance(meta, dict):
                path = meta.get("path")
                colour = meta.get("colour")

            graph = NetworkGenerator.loadEdges(path)

            for up, downstream_list in graph.items():
                for ds, lid in downstream_list:
                    # Avoid duplicates if the same ID appears multiple times across files
                    if lid in seen_ids:
                        continue
                    seen_ids.add(lid)

                    all_links.append({
                        "id": str(lid).strip(),
                        "upstream": str(up).strip(),
                        "downstream": str(ds).strip(),
                        "type": str(linkType).strip(),
                        "colour": colour,
                    })

        return all_links
