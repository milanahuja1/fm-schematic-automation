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


    @staticmethod
    def generateConduits(links, userControls, flumes, flapValves, orfices, pumps, sluices, weirs):
        """Create a unified list of conduit records for drawing.

        Args:
            links: adjacency dict in the same format as `loadEdges` returns:
                { upstream: [(downstream, link_id), ...], ... }
            userControls/flumes/flapValves/orfices/pumps/sluices/weirs:
                Datasets describing special conduit types. These can be:
                - dicts keyed by link id (common)
                - sets of link ids
                - lists/tuples of link ids
                - None

        Returns:
            conduits: list of dicts:
                [{"id": str, "upstream": str, "downstream": str, "type": str}, ...]
        """

        def _id_set(obj):
            if obj is None:
                return set()

            # If it's an adjacency dict like loadEdges: {upstream: [(downstream, link_id), ...], ...}
            if isinstance(obj, dict):
                ids = set()
                looks_like_adj = False

                for outs in obj.values():
                    if isinstance(outs, list) and outs:
                        first = outs[0]
                        if isinstance(first, tuple) and len(first) >= 2:
                            looks_like_adj = True

                    if isinstance(outs, list):
                        for item in outs:
                            if isinstance(item, tuple) and len(item) >= 2:
                                ids.add(str(item[1]).strip())

                if looks_like_adj:
                    return ids

                # Otherwise assume dict is keyed by id
                return set(str(k).strip() for k in obj.keys())

            # If it's already an iterable of ids
            try:
                return set(str(x).strip() for x in obj)
            except TypeError:
                return set()

        userControlIDs = _id_set(userControls)
        flumeIDs = _id_set(flumes)
        flapValveIDs = _id_set(flapValves)
        orificeIDs = _id_set(orfices)
        pumpIDs = _id_set(pumps)
        sluiceIDs = _id_set(sluices)
        weirIDs = _id_set(weirs)

        conduits = []

        # Flatten the adjacency list into a single conduit list
        for upstream, outs in (links or {}).items():
            up = str(upstream).strip()
            for downstream, link_id in outs:
                ds = str(downstream).strip()
                lid = str(link_id).strip()

                # Determine conduit type (priority order)
                conduitType = "link"
                if lid in userControlIDs:
                    conduitType = "user_control"
                elif lid in flapValveIDs:
                    conduitType = "flap_valve"
                elif lid in pumpIDs:
                    conduitType = "pump"
                elif lid in sluiceIDs:
                    conduitType = "sluice"
                elif lid in weirIDs:
                    conduitType = "weir"
                elif lid in flumeIDs:
                    conduitType = "flume"
                elif lid in orificeIDs:
                    conduitType = "orifice"

                conduits.append({
                    "id": lid,
                    "upstream": up,
                    "downstream": ds,
                    "type": conduitType,
                })

        return conduits
