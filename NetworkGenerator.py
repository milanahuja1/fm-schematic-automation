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