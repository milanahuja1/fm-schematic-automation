import csv


class NetworkGenerator:

    @staticmethod
    def load_edges(filename):
        """
        Reads a pipe/link CSV and returns a directed adjacency list.

        Supports two column formats (auto-detected from headers):
            Legacy:  upstream, downstream, id
            Muston:  US node ID, DS node ID, Link suffix

        Returns:
            { source_node_id: [(target_node_id, edge_id), ...], ... }
        """
        graph = {}

        with open(filename, newline="", encoding="utf-8-sig") as file:
            reader = csv.DictReader(file)
            headers = reader.fieldnames or []

            # Auto-detect column names
            if "US node ID" in headers:
                us_col, ds_col, id_col = "US node ID", "DS node ID", "Link suffix"
            else:
                us_col, ds_col, id_col = "upstream", "downstream", "id"

            for row in reader:
                source = row[us_col].strip()
                target = row[ds_col].strip()
                edge_id = row[id_col].strip()

                if not source or not target:
                    continue

                if source not in graph:
                    graph[source] = []

                graph[source].append((target, edge_id))

        return graph

    @staticmethod
    def load_nodes_with_xy(filename):
        """
        Reads a node CSV and returns a node map.

        Supports two column formats (auto-detected from headers):
            Legacy:  id, type, x, y
            Muston:  Node ID, Node type, x (m), y (m)

        For the Muston format the string node type is mapped to an integer:
            "manhole" (and anything unrecognised) -> 1

        Returns:
            { node_id: {"type": int, "x": float, "y": float}, ... }
        """
        # Muston node-type string -> integer mapping
        NODE_TYPE_MAP = {
            "manhole": 1,
        }

        node_map = {}

        with open(filename, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames or []

            # Auto-detect column names
            if "Node ID" in headers:
                id_col, type_col, x_col, y_col = "Node ID", "Node type", "x (m)", "y (m)"
                muston_format = True
            else:
                id_col, type_col, x_col, y_col = "id", "type", "x", "y"
                muston_format = False

            for row in reader:
                node_id = row[id_col].strip()
                if not node_id:
                    continue

                raw_x = row[x_col].strip()
                raw_y = row[y_col].strip()
                if not raw_x or not raw_y:
                    continue

                if muston_format:
                    raw_type = row[type_col].strip().lower()
                    node_type = NODE_TYPE_MAP.get(raw_type, 1)
                else:
                    node_type = int(row[type_col])

                node_map[node_id] = {
                    "type": node_type,
                    "x": float(raw_x),
                    "y": float(raw_y),
                }

        return node_map

    @staticmethod
    def loadSensorData(filename):
        """
        Reads a sensor/monitor CSV and returns a sensor map.

        Supports two column formats (auto-detected from headers):
            Legacy:  nodeID, sensorID
            Muston:  Node ID, Asset ID  (every row in the monitors file is a monitor)

        Returns:
            { node_id: [sensor_id, ...], ... }
        """
        sensor_map = {}

        with open(filename, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames or []

            # Auto-detect column names
            if "Node ID" in headers:
                id_col = "Node ID"
                sensor_col = "Asset ID" if "Asset ID" in headers else "Node ID"
            else:
                id_col = "nodeID"
                sensor_col = "sensorID"

            for row in reader:
                node_id = row[id_col].strip()
                sensor_id = row[sensor_col].strip()

                if not node_id:
                    continue

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

        # Build set of all nodes that appear anywhere in the original graph
        # (as either an upstream source or a downstream target)
        all_graph_nodes = set(graph.keys())
        for outs in graph.values():
            for downstream, _ in outs:
                all_graph_nodes.add(downstream)

        for start in sensor_nodes:
            reduced_graph[start] = []

            # DFS downstream from this sensor node
            stack = [(start, 0)]  # (current_node, path_length)
            visited = set()  # prevent infinite loops on cyclic graphs

            while stack:
                current, depth = stack.pop()

                if current in visited:
                    continue
                visited.add(current)

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

        # Include sensor nodes that appear in the network topology but whose
        # DFS path to another sensor was broken (e.g. a source monitor with no
        # upstream sensors and a gap in the edge data between it and the next
        # downstream sensor).  These nodes will render without pipes until the
        # edge data is complete, but at least they won't be silently dropped.
        for node in sensor_nodes:
            if node not in used_nodes and node in all_graph_nodes:
                used_nodes.add(node)

        # Build reduced node dictionary in same format as load_nodes_with_xy
        reduced_nodes = {}
        for node_id in used_nodes:
            if node_id in nodes:
                reduced_nodes[node_id] = nodes[node_id]

        return reduced_graph, reduced_nodes
