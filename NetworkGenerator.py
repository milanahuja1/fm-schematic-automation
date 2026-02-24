import csv

class NetworkGenerator:

    @staticmethod
    def loadEdges(filename):

        graph = {}

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
    def loadNodes(filename):
        """
        Reads a node CSV with columns: Node ID, Node type
        Returns:
            { node_id: {"type": int}, ... }
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
                nodeMap[nodeID] = {
                    "type": nodeType
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
