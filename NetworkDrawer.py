from PyQt6.QtWidgets import QGraphicsScene, QGraphicsView
from PyQt6.QtGui import QPainter, QPen
from PyQt6.QtCore import Qt, QPointF

from SvgNodeFactory import SvgNodeFactory


import networkx as nx
from networkx.drawing.nx_pydot import graphviz_layout


class NetworkDrawer:
    @staticmethod
    def drawNetwork(graph, nodes):
        """
        graph format:
            { upstream: [(downstream, edge_id), ...], ... }

        nodes format:
            {
                node_id: {
                    "type": 1|2|3,
                    "x": float,
                    "y": float
                }
            }

        Returns:
            QGraphicsView (ready to embed in a window)
        """
        # --------------------------
        # Auto layout using Graphviz (flow diagram)
        # --------------------------
        G = nx.DiGraph()
        for upstream, outs in graph.items():
            for downstream, edge_id in outs:
                G.add_edge(str(upstream), str(downstream))

        if len(G.nodes) > 0:
            pos = graphviz_layout(
                G,
                prog="dot",
            )

            # Some NetworkX versions (nx_pydot) don't support passing Graphviz args.
            # `dot` defaults to a top-to-bottom layout. To mimic LR flow, swap axes.
            pos = {n: (y, x) for n, (x, y) in pos.items()}

            min_x = min(x for x, y in pos.values())
            min_y = min(y for x, y in pos.values())

            scale = 1.5

            for node_id in nodes:
                sid = str(node_id)
                if sid in pos:
                    x, y = pos[sid]
                    nodes[node_id]["x"] = (x - min_x) * scale
                    nodes[node_id]["y"] = (y - min_y) * scale

        scene = QGraphicsScene()

        # --------------------------
        # Draw Pipes
        # --------------------------
        pen = QPen(Qt.GlobalColor.black)
        pen.setWidth(1)

        for upstreamNode, outs in graph.items():
            if upstreamNode not in nodes:
                continue

            # centres in scene coords (flip Y to match how SVG nodes are drawn)
            startX = nodes[upstreamNode]["x"]
            startY = -nodes[upstreamNode]["y"]

            for downstreamNode, edge_id in outs:
                if downstreamNode not in nodes:
                    continue

                endX = nodes[downstreamNode]["x"]
                endY = -nodes[downstreamNode]["y"]

                scene.addLine(startX, startY, endX, endY, pen)









        # --------------------------
        # Draw SVG nodes on top
        # --------------------------
        for node_id, data in nodes.items():
            node_type = data["type"]
            x = data["x"]
            y = -data["y"]

            tooltip_text = None
            # If you store extra hover info in the node dict, use it.
            # Example: nodes[node_id] = {"type": 1, "x": 0, "y": 0, "tooltip": "..."}
            if "tooltip" in data:
                tooltip_text = data["tooltip"]

            item = SvgNodeFactory.create(node_id, node_type, x, y, tooltip_text=tooltip_text)
            scene.addItem(item)

        view = QGraphicsView(scene)
        view.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        return view