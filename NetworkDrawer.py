from PyQt6.QtWidgets import QGraphicsScene, QGraphicsView
from PyQt6.QtGui import QPainter, QColor
from PyQt6.QtCore import Qt

from SvgNodeFactory import SvgNodeFactory
from PipeItem import PipeItem

import math
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

        # Only keep nodes that are actually referenced by a compressed edge.
        # This drops important-typed nodes (e.g. outfalls) that have no path
        # to or from any monitor.
        edge_node_ids = set()
        for c in compressed_conduits:
            edge_node_ids.add(c["upstream"])
            edge_node_ids.add(c["downstream"])

        compressed_nodes = {
            nid: data for nid, data in nodes.items()
            if str(nid) in edge_node_ids or nid in edge_node_ids
        }

        print(f"--- COMPRESSION: {len(nodes)} nodes → {len(compressed_nodes)}, "
              f"{len(conduits or [])} conduits → {len(compressed_conduits)} ---")

        return compressed_conduits, compressed_nodes

    @staticmethod
    def _removeOverlaps(nodes, min_sep=60.0, max_iterations=200):
        """
        Iteratively push every pair of nodes that are closer than min_sep pixels
        apart until no overlaps remain (or max_iterations is reached).

        Handles all cases including exactly coincident nodes. Each iteration is
        O(n²) over the node list, with early exit when nothing moved.
        """
        nids = list(nodes.keys())
        n = len(nids)
        if n < 2:
            return

        for _ in range(max_iterations):
            any_moved = False

            for i in range(n):
                for j in range(i + 1, n):
                    a, b = nids[i], nids[j]
                    dx = nodes[b]["x"] - nodes[a]["x"]
                    dy = nodes[b]["y"] - nodes[a]["y"]
                    dist = math.sqrt(dx * dx + dy * dy)

                    if dist < min_sep:
                        if dist < 1e-6:
                            # Coincident: push along a deterministic angle so
                            # pairs spread rather than all collapsing to one side
                            angle = 2 * math.pi * j / n
                            dx, dy, dist = math.cos(angle), math.sin(angle), 1.0

                        push = (min_sep - dist) / 2.0
                        nx_ = dx / dist
                        ny_ = dy / dist
                        nodes[a]["x"] -= nx_ * push
                        nodes[a]["y"] -= ny_ * push
                        nodes[b]["x"] += nx_ * push
                        nodes[b]["y"] += ny_ * push
                        any_moved = True

            if not any_moved:
                break

    @staticmethod
    def _fixedLengthLayout(nodes, conduits, edge_px=150.0):
        """
        Place nodes so every display edge is exactly edge_px pixels long,
        while using real-world coordinates to determine the direction of each hop.

        Uses a topological traversal (Kahn's algorithm) so every node is placed
        only after all its upstream parents have been placed. Nodes with multiple
        upstream parents get the average of all parent suggestions, which handles
        confluences naturally.

        Disconnected sub-graphs and any nodes caught in cycles are placed in a
        row below the main layout.
        """
        from collections import defaultdict, deque

        if not nodes:
            return

        by_str = {str(nid): nid for nid in nodes}
        all_str = set(by_str.keys())

        # Build directed adjacency and track in-degrees
        out_adj = defaultdict(list)
        in_adj  = defaultdict(list)
        for c in (conduits or []):
            u = str(c.get("upstream",   "")).strip()
            d = str(c.get("downstream", "")).strip()
            if u in by_str and d in by_str and u != d:
                out_adj[u].append(d)
                in_adj[d].append(u)

        in_degree   = {n: len(in_adj[n]) for n in all_str}
        suggestions = defaultdict(list)   # node_str -> [(x, y), ...]
        placed      = {}                  # node_str -> (x, y)

        # Seed root nodes (no incoming edges) spread horizontally
        roots = sorted(n for n in all_str if in_degree[n] == 0)
        for i, root in enumerate(roots):
            suggestions[root].append((i * edge_px * 2.5, 0.0))

        queue = deque(roots)

        while queue:
            u = queue.popleft()

            if u in placed:
                continue

            # Wait until all parents have been placed
            if any(p not in placed for p in in_adj[u]):
                queue.append(u)   # re-enqueue; will retry once parents land
                continue

            # Average all parent suggestions (or the seed for roots)
            sx = sum(s[0] for s in suggestions[u]) / len(suggestions[u])
            sy = sum(s[1] for s in suggestions[u]) / len(suggestions[u])
            placed[u] = (sx, sy)

            u_data = nodes[by_str[u]]

            for d in out_adj[u]:
                if d in placed:
                    continue

                d_data = nodes[by_str[d]]
                wdx = d_data["x"] - u_data["x"]
                wdy = d_data["y"] - u_data["y"]
                wdist = math.sqrt(wdx * wdx + wdy * wdy)

                if wdist < 1e-6:
                    # Co-located in the world: default to flowing right
                    wdx, wdy, wdist = 1.0, 0.0, 1.0

                suggestions[d].append((
                    sx + edge_px * wdx / wdist,
                    sy + edge_px * wdy / wdist,
                ))

                in_degree[d] -= 1
                if in_degree[d] == 0:
                    queue.append(d)

        # Place any remaining nodes (cycles / disconnected islands)
        unplaced = all_str - set(placed)
        if unplaced:
            max_y = max((placed[n][1] for n in placed), default=0)
            for i, nid in enumerate(sorted(unplaced)):
                placed[nid] = (i * edge_px, max_y + edge_px * 2)

        # Write back to the nodes dict
        for sid, (x, y) in placed.items():
            nodes[by_str[sid]]["x"] = x
            nodes[by_str[sid]]["y"] = y

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

        # --------------------------
        # Layout: spatial (real-world coords) or Graphviz fallback
        # --------------------------
        all_x = [nodes[n]["x"] for n in nodes]
        all_y = [nodes[n]["y"] for n in nodes]
        non_zero = sum(1 for x, y in zip(all_x, all_y) if x != 0.0 or y != 0.0)
        use_spatial = len(nodes) > 0 and non_zero > len(nodes) * 0.5

        if use_spatial:
            # Fixed-length layout: every edge = 150 px, direction from real-world coords
            NetworkDrawer._fixedLengthLayout(nodes, conduits)

        elif len(G.nodes) > 0:
            pos = graphviz_layout(G, prog="dot")

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

        # Iteratively push overlapping nodes apart until none remain
        NetworkDrawer._removeOverlaps(nodes)

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