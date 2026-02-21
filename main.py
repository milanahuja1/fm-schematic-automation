from NetworkGenerator import NetworkGenerator
from ShapeDrawer import ShapeDrawer

graph = NetworkGenerator.load_edges("edgeTable.csv")
nodes = NetworkGenerator.load_nodes("nodeTable.csv")
# ---------- Run ----------
ShapeDrawer.draw_graph(graph, nodes)