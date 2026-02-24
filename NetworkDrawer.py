from PyQt6.QtWidgets import QGraphicsScene, QGraphicsView
from PyQt6.QtGui import QPainter
from PyQt6.QtCore import Qt

from SvgNodeFactory import SvgNodeFactory
from PipeItem import PipeItem

import networkx as nx
from networkx.drawing.nx_pydot import graphviz_layout


class NetworkDrawer:
    @staticmethod
    def drawNetwork(graph, nodes, monitors):
        """
        graph format:
            { upstream: [(downstream, edge_id), ...], ... }

        nodes format:
            {
                node_id: {
                    "type": 1|2|3,
                    # optional fields:
                    "tooltip": str
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

        # Ensure x/y exist even if the input nodes table has no coordinates
        for node_id in nodes:
            nodes[node_id].setdefault("x", 0.0)
            nodes[node_id].setdefault("y", 0.0)

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
        # Create SVG node items (store references)
        # --------------------------
        node_items = {}
        for node_id, data in nodes.items():
            node_type = data["type"]

            # If this node is a monitor and is a Manhole, override type
            if monitors and node_id in monitors:
                if isinstance(node_type, str) and node_type.strip().lower() == "manhole":
                    node_type = "flowmonitor"

            x = data.get("x", 0.0)
            y = -data.get("y", 0.0)

            tooltip_text = data.get("tooltip")

            item = SvgNodeFactory.create(node_id, node_type, x, y, tooltip_text=tooltip_text)
            scene.addItem(item)
            node_items[node_id] = item

        # --------------------------
        # Create Pipes (edges) and register them on nodes
        # --------------------------
        for upstreamNode, outs in graph.items():
            if upstreamNode not in node_items:
                continue

            for downstreamNode, edge_id in outs:
                if downstreamNode not in node_items:
                    continue

                pipe = PipeItem(
                    upstream_item=node_items[upstreamNode],
                    downstream_item=node_items[downstreamNode],
                    edge_id=edge_id,
                    base_width=1,
                    hover_width=2,
                    arrow_size=10.0,
                    hit_width=12.0,
                    draw_label=False,
                )
                scene.addItem(pipe)

                # Either endpoint moving should update the pipe
                node_items[upstreamNode].connectedPipes.append(pipe)
                node_items[downstreamNode].connectedPipes.append(pipe)

        view = QGraphicsView(scene)
        view.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        return view