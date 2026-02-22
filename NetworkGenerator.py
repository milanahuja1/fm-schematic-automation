import csv

class NetworkGenerator:

    @staticmethod
    def load_edges(filename):

        graph = {}

        with open(filename, newline="") as file:
            reader = csv.DictReader(file)

            for row in reader:
                source = row["upstream"]
                target = row["downstream"]
                weight = float(row["id"])

                if source not in graph:
                    graph[source] = []

                graph[source].append((target, weight))

        return graph

    @staticmethod
    def load_nodes_with_xy(filename):
        """
        Reads a node CSV with columns: id,type,x,y
        Returns:
            { node_id: {"type": int, "x": float, "y": float}, ... }
        """
        node_map = {}

        with open(filename, newline="") as f:
            reader = csv.DictReader(f)
            # Expecting: id,type,x,y
            for row in reader:
                node_id = row["id"]
                node_map[node_id] = {
                    "type": int(row["type"]),
                    "x": float(row["x"]),
                    "y": float(row["y"]),
                }

        return node_map

    @staticmethod
    def loadSensorData(filename):
        """
        Reads a sensor CSV with columns: nodeID,sensorID
        Returns:
            { node_id: [sensor_id, ...], ... }
        """
        sensor_map = {}

        with open(filename, newline="") as f:
            reader = csv.DictReader(f)
            # Expecting: nodeID,sensorID
            for row in reader:
                node_id = row["nodeID"]
                sensor_id = row["sensorID"]

                if node_id not in sensor_map:
                    sensor_map[node_id] = []

                sensor_map[node_id].append(sensor_id)

        return sensor_map

    @staticmethod
    def build_sensor_reduced_graph(graph, nodes, sensors):
        """
        Builds a reduced graph containing only sensor nodes.

        Parameters:
            graph   : { upstream: [(downstream, edge_id), ...] }
            nodes   : full node map from load_nodes_with_xy
            sensors : { node_id: [sensor_id, ...] }

        Returns:
            (reduced_graph, reduced_nodes)
                reduced_graph: { sensor_node: [(next_sensor_node, path_length), ...] }
                reduced_nodes: dict of node_id to {"type": int, "x": float, "y": float}
        """

        sensor_nodes = set(sensors.keys())
        reduced_graph = {}
        added_edges = set()  # prevent duplicates
        used_nodes = set()

        for start in sensor_nodes:
            reduced_graph[start] = []

            # DFS downstream from this sensor node
            stack = [(start, 0)]  # (current_node, path_length)

            while stack:
                current, depth = stack.pop()

                if current not in graph:
                    continue

                for downstream, edge_id in graph[current]:

                    # If we hit another sensor node (and it's not the start itself)
                    if downstream in sensor_nodes and downstream != start:
                        edge_key = (start, downstream)
                        if edge_key not in added_edges:
                            reduced_graph[start].append((downstream, depth + 1))
                            added_edges.add(edge_key)
                            used_nodes.add(start)
                            used_nodes.add(downstream)
                        continue

                    # Otherwise keep traversing
                    stack.append((downstream, depth + 1))

        # Ensure nodes with no outgoing edges but that are sensors still appear
        for node in sensor_nodes:
            if node not in used_nodes and node in reduced_graph:
                if reduced_graph[node]:
                    used_nodes.add(node)

        # Build reduced node dictionary in same format as load_nodes_with_xy
        reduced_nodes = {}
        for node_id in used_nodes:
            if node_id in nodes:
                reduced_nodes[node_id] = nodes[node_id]

        return reduced_graph, reduced_nodes
