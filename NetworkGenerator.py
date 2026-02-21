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
    def load_nodes(filename):
        """
        Reads nodes.csv with columns: id,type
        Returns a dict: { node_id: type }
        """
        node_map = {}

        with open(filename, newline="") as file:
            reader = csv.DictReader(file)

            for row in reader:
                node_id = row["id"]
                node_type = int(row["type"])
                node_map[node_id] = node_type

        return node_map