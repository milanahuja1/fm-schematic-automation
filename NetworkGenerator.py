import csv

class NetworkGenerator:

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


    @staticmethod
    def generateConduits(links, userControls, flumes, flapValves, orfices, pumps, sluices, weirs):
        """
        Merge all conduit datasets into one unified conduit list.
        Each dataset is expected to be in the adjacency format returned by loadEdges:
            { upstream: [(downstream, link_id), ...], ... }
        """

        conduits = []
        seen_ids = set()

        def _add_dataset(dataset, conduit_type):
            if not dataset:
                return

            for upstream, outs in dataset.items():
                up = str(upstream).strip()
                for downstream, link_id in outs:
                    ds = str(downstream).strip()
                    lid = str(link_id).strip()

                    # Avoid duplicates (special types override plain links)
                    if lid in seen_ids:
                        continue

                    conduits.append({
                        "id": lid,
                        "upstream": up,
                        "downstream": ds,
                        "type": conduit_type,
                    })

                    seen_ids.add(lid)

        # Add specialised conduit types first (so they take priority)
        _add_dataset(userControls, "user_control")
        _add_dataset(flapValves, "flap_valve")
        _add_dataset(pumps, "pump")
        _add_dataset(sluices, "sluice")
        _add_dataset(weirs, "weir")
        _add_dataset(flumes, "flume")
        _add_dataset(orfices, "orifice")

        # Finally add plain links (only if not already added)
        _add_dataset(links, "link")

        return conduits
