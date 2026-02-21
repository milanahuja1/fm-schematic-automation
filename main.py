from NetworkGenerator import NetworkGenerator
from ShapeDrawer import ShapeDrawer

graph = NetworkGenerator.load_edges("data/edgeTable.csv")
nodes = NetworkGenerator.load_nodes("data/nodeTable.csv")
# ---------- Run ----------
ShapeDrawer.draw_graph(graph, nodes)