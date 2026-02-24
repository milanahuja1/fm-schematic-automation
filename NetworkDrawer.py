from PyQt6.QtWidgets import QGraphicsScene, QGraphicsView
from PyQt6.QtGui import QPainter, QColor
from PyQt6.QtCore import Qt

from SvgNodeFactory import SvgNodeFactory
from PipeItem import PipeItem

import networkx as nx
from networkx.drawing.nx_pydot import graphviz_layout


class NetworkDrawer:
    @staticmethod
    def _compressToMonitors(conduits, nodes, monitors):
        """
        Collapse the full network down to only monitor nodes and non-manhole nodes.
        Chains of plain manholes between important nodes are replaced with a direct edge.
        Returns (compressed_conduits, compressed_nodes).
        """
        G = nx.DiGraph()
        for c in (conduits or []):
            up = str(c.get("upstream", "")).strip()
            ds = str(c.get("downstream", "")).strip()
            if up and ds:
                G.add_edge(up, ds)

        monitor_ids = {str(k) for k in (monitors or {})}

        def is_important(node_id):
            if str(node_id) in monitor_ids:
                return True
            data = nodes.get(node_id) or nodes.get(str(node_id), {})
            return str(data.get("type", "")).strip().lower() != "manhole"

        important = {n for n in G.nodes if is_important(n)}

        compressed_conduits = []
        seen_edges = set()

        for start in important:
            visited = {start}
            frontier = list(G.successors(start))

            while frontier:
                next_frontier = []
                for node in frontier:
                    if node in visited:
                        continue
                    visited.add(node)
                    if node in important:
                        edge_key = (start, node)
                        if edge_key not in seen_edges:
                            seen_edges.add(edge_key)
                            compressed_conduits.append({
                                "id": f"{start}_to_{node}",
                                "upstream": start,
                                "downstream": node,
                                "type": "link",
                            })
                    else:
                        next_frontier.extend(G.successors(node))
                frontier = next_frontier

        compressed_nodes = {nid: data for nid, data in nodes.items() if is_important(nid)}

        print(f"--- COMPRESSION: {len(nodes)} nodes → {len(compressed_nodes)}, "
              f"{len(conduits or [])} conduits → {len(compressed_conduits)} ---")

        return compressed_conduits, compressed_nodes

    @staticmethod
    def drawNetwork(conduits, nodes, monitors, compressed=False):
        """
        conduits format:
            [
                {"id": str, "upstream": str, "downstream": str, "type": str},
                ...
            ]
        compressed: if True, collapse plain-manhole chains and show only monitors
                    and non-manhole nodes.
        """

        if compressed:
            conduits, nodes = NetworkDrawer._compressToMonitors(conduits, nodes, monitors)

        # --------------------------
        # Auto layout using Graphviz (flow diagram)
        # --------------------------
        G = nx.DiGraph()
        for c in (conduits or []):
            up = str(c.get("upstream", "")).strip()
            ds = str(c.get("downstream", "")).strip()
            if up and ds:
                G.add_edge(up, ds)

        # --------------------------
        # DEBUG: Graph diagnostics
        # --------------------------
        print("--- GRAPH DEBUG ---")
        print(f"Total nodes in NetworkX graph: {G.number_of_nodes()}")
        print(f"Total edges in NetworkX graph: {G.number_of_edges()}")

        weak_components = list(nx.weakly_connected_components(G))
        print(f"Weakly connected components: {len(weak_components)}")

        for i, comp in enumerate(weak_components[:5]):
            print(f"Component {i+1} size: {len(comp)}")
            print(f"Sample nodes: {list(comp)[:5]}")

        print("-------------------")

        # Ensure x/y exist even if the input nodes table has no coordinates
        for node_id in nodes:
            nodes[node_id].setdefault("x", 0.0)
            nodes[node_id].setdefault("y", 0.0)

        if len(G.nodes) > 0:
            pos = graphviz_layout(
                G,
                prog="dot",
            )

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
        node_items_str = {}
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
            node_items_str[str(node_id)] = item

        # --------------------------
        # Create Pipes (conduits) and register them on nodes
        # --------------------------
        conduit_colours = {
            "link": QColor("#7a7a7a"),
            "user_control": QColor("#9467bd"),
            "flap_valve": QColor("#8c564b"),
            "pump": QColor("#d62728"),
            "sluice": QColor("#ff7f0e"),
            "weir": QColor("#1f77b4"),
            "flume": QColor("#2ca02c"),
            "orifice": QColor("#bcbd22"),
        }

        for c in (conduits or []):
            up = str(c.get("upstream", "")).strip()
            ds = str(c.get("downstream", "")).strip()
            edge_id = c.get("id")
            ctype = str(c.get("type", "link")).strip().lower()
            colour = conduit_colours.get(ctype, conduit_colours["link"])

            if not up or not ds:
                continue

            up_item = node_items_str.get(up)
            ds_item = node_items_str.get(ds)

            if up_item is None or ds_item is None:
                continue

            pipe = PipeItem(
                upstream_item=up_item,
                downstream_item=ds_item,
                edge_id=edge_id,
                pen_colour=colour,
                base_width=1,
                hover_width=2,
                arrow_size=10.0,
                hit_width=12.0,
                draw_label=False,
            )
            scene.addItem(pipe)

            up_item.connectedPipes.append(pipe)
            ds_item.connectedPipes.append(pipe)

        view = QGraphicsView(scene)
        view.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        return view