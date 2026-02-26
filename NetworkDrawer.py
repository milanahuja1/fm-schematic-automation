from collections import defaultdict, deque

from PyQt6.QtWidgets import QGraphicsScene, QGraphicsView
from PyQt6.QtGui import QPainter, QColor

from SvgNodeFactory import SvgNodeFactory
from PipeItem import PipeItem

import math
import networkx as nx
from networkx.drawing.nx_pydot import graphviz_layout


# Colour assigned to each conduit type when drawn
CONDUIT_COLOURS = {
    "conduit":      QColor("#7a7a7a"),
    "user_control": QColor("#9467bd"),
    "flap_valve":   QColor("#8c564b"),
    "pump":         QColor("#d62728"),
    "sluice":       QColor("#ff7f0e"),
    "weir":         QColor("#1f77b4"),
    "flume":        QColor("#2ca02c"),
    "orifice":      QColor("#bcbd22"),
}


class NetworkDrawer:

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    @staticmethod
    def drawNetwork(conduits, nodes, monitors, monitorInformation, compressed=False):
        """
        Build and return a QGraphicsView containing the network schematic.

        conduits : list of {"id", "upstream", "downstream", "type"}
        nodes    : dict  node_id -> {"type", "x", "y", ...}
        monitors : dict  node_id -> {...}   (nodes that carry flow monitors)
        monitorInformation : dict
            Mapping of manhole node_id -> {
                "monitorName": str   # user-defined monitor label
                "note": str          # free-text comment entered by user
                "link": str          # selected conduit ID the monitor is attached to
            }
        compressed: if True, collapse manhole chains so only monitors and
                    non-manhole structures are shown.
        """
        # Split pipes and insert monitor nodes before anything else so that
        # compression and layout both see monitors as first-class nodes.
        conduits, nodes, inserted_manholes = NetworkDrawer._insertMonitorNodes(
            conduits, nodes, monitorInformation
        )

        if compressed:
            conduits, nodes = NetworkDrawer._compressToMonitors(conduits, nodes, monitors)

        G = NetworkDrawer._buildGraph(conduits)
        NetworkDrawer._logGraphDebug(G)
        NetworkDrawer._ensureCoordinates(nodes)
        NetworkDrawer._applyLayout(G, nodes, conduits)
        NetworkDrawer._flattenAlignedSegments(nodes, conduits)
        NetworkDrawer._removeOverlaps(nodes)

        scene = QGraphicsScene()
        node_items, node_items_str = NetworkDrawer._buildNodeItems(
            scene, nodes, monitors, inserted_manholes
        )
        NetworkDrawer._buildPipeItems(scene, conduits, node_items_str)

        view = QGraphicsView(scene)
        view.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        return view

    # ------------------------------------------------------------------
    # Monitor node insertion
    # ------------------------------------------------------------------

    @staticmethod
    def _insertMonitorNodes(conduits, nodes, monitorInformation):
        """
        For every entry in monitorInformation, replace the associated manhole
        node with a flowmonitor node at the same world position.  All conduits
        that previously referenced the manhole (both inflows and outflows) are
        re-wired to reference the monitor instead, so the monitor inherits the
        manhole's full set of connections.

        This means a confluence manhole (multiple inflows) becomes a confluence
        monitor — all upstream streams flow directly into the monitor node,
        which is correct: the monitor IS the measurement point where those
        streams combine.

            Monitor_A ──┐
                        ├──► Monitor_B ──► downstream
            other_MH  ──┘

        Self-loop edges and duplicate edges produced by the substitution are
        silently dropped.

        Returns:
            (modified_conduits, modified_nodes, replaced_manholes)
            where replaced_manholes is the set of str manhole IDs that were
            removed (used to suppress the legacy type-override in
            _resolveNodeType).
        """
        if not monitorInformation:
            return conduits, nodes, set()

        modified_nodes    = dict(nodes)
        replaced_manholes = set()
        manhole_to_monitor = {}   # str(manhole_id) -> monitor_id

        for manhole_id, info in monitorInformation.items():
            manhole_str = str(manhole_id)
            monitor_id  = str(info.get("monitorName", "") or f"monitor_{manhole_id}").strip()

            manhole_key  = next((k for k in nodes if str(k) == manhole_str), None)
            manhole_data = nodes.get(manhole_key, {}) if manhole_key is not None else {}

            note = info.get("note", "").strip()
            tooltip_parts = [f"Manhole: {manhole_id}"]
            if note:
                tooltip_parts.append(f"Note: {note}")

            # Place the monitor at the manhole's world position
            modified_nodes[monitor_id] = {
                "type":    "flowmonitor",
                "x":       manhole_data.get("x", 0.0),
                "y":       manhole_data.get("y", 0.0),
                "tooltip": "\n".join(tooltip_parts),
            }

            # Remove the manhole — the monitor takes its place entirely
            if manhole_key is not None:
                modified_nodes.pop(manhole_key, None)

            replaced_manholes.add(manhole_str)
            manhole_to_monitor[manhole_str] = monitor_id

        # Re-wire every conduit that referenced a manhole to reference its monitor
        modified_conduits = []
        seen_edges = set()

        for c in conduits:
            c = dict(c)
            up_str = manhole_to_monitor.get(str(c.get("upstream",   "")).strip(),
                                            str(c.get("upstream",   "")).strip())
            ds_str = manhole_to_monitor.get(str(c.get("downstream", "")).strip(),
                                            str(c.get("downstream", "")).strip())
            c["upstream"]   = up_str
            c["downstream"] = ds_str

            # Drop self-loops (both ends resolved to the same monitor)
            if up_str == ds_str:
                continue

            # Drop duplicates
            key = (up_str, ds_str)
            if key in seen_edges:
                continue
            seen_edges.add(key)

            modified_conduits.append(c)

        return modified_conduits, modified_nodes, replaced_manholes

    # ------------------------------------------------------------------
    # Graph construction
    # ------------------------------------------------------------------

    @staticmethod
    def _buildGraph(conduits):
        """Return a directed NetworkX graph from the conduit list."""
        G = nx.DiGraph()
        for c in (conduits or []):
            up = str(c.get("upstream",   "")).strip()
            ds = str(c.get("downstream", "")).strip()
            if up and ds:
                G.add_edge(up, ds)
        return G

    @staticmethod
    def _logGraphDebug(G):
        """Print basic graph diagnostics to stdout."""
        print("--- GRAPH DEBUG ---")
        print(f"Nodes: {G.number_of_nodes()}  Edges: {G.number_of_edges()}")
        components = list(nx.weakly_connected_components(G))
        print(f"Weakly connected components: {len(components)}")
        for i, comp in enumerate(components[:5]):
            print(f"  Component {i + 1}: {len(comp)} nodes  sample={list(comp)[:3]}")
        print("-------------------")

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    @staticmethod
    def _ensureCoordinates(nodes):
        """Set x/y to 0.0 on any node that is missing them."""
        for data in nodes.values():
            data.setdefault("x", 0.0)
            data.setdefault("y", 0.0)

    @staticmethod
    def _applyLayout(G, nodes, conduits):
        """
        Choose between spatial (fixed-length) layout and the Graphviz fallback.
        Spatial layout is used when more than half the nodes carry real coordinates.
        """
        all_x = [nodes[n]["x"] for n in nodes]
        all_y = [nodes[n]["y"] for n in nodes]
        non_zero = sum(1 for x, y in zip(all_x, all_y) if x != 0.0 or y != 0.0)
        use_spatial = len(nodes) > 0 and non_zero > len(nodes) * 0.5

        if use_spatial:
            NetworkDrawer._fixedLengthLayout(nodes, conduits)
        elif len(G.nodes) > 0:
            NetworkDrawer._graphvizLayout(G, nodes)

    @staticmethod
    def _graphvizLayout(G, nodes, scale=1.5):
        """Apply a Graphviz dot layout, swapping axes so flow runs left-to-right."""
        pos = graphviz_layout(G, prog="dot")
        pos = {n: (y, x) for n, (x, y) in pos.items()}   # top-to-bottom → left-to-right

        min_x = min(x for x, _ in pos.values())
        min_y = min(y for _, y in pos.values())

        for node_id in nodes:
            sid = str(node_id)
            if sid in pos:
                x, y = pos[sid]
                nodes[node_id]["x"] = (x - min_x) * scale
                nodes[node_id]["y"] = (y - min_y) * scale

    @staticmethod
    def _fixedLengthLayout(nodes, conduits, edge_px=150.0):
        """
        Place nodes so every display edge is exactly edge_px pixels long,
        using real-world coordinates to determine the direction of each hop.

        Uses Kahn's topological traversal so every node is placed only after
        all its upstream parents have been placed. Confluence nodes (multiple
        parents) land at the average of their parents' suggestions.
        Cycles and disconnected islands are appended below the main layout.
        """
        if not nodes:
            return

        by_str   = {str(nid): nid for nid in nodes}
        all_str  = set(by_str.keys())
        out_adj, in_adj = NetworkDrawer._buildAdjacency(conduits, by_str)

        in_degree   = {n: len(in_adj[n]) for n in all_str}
        suggestions = defaultdict(list)
        placed      = {}

        # Seed roots horizontally
        roots = sorted(n for n in all_str if in_degree[n] == 0)
        for i, root in enumerate(roots):
            suggestions[root].append((i * edge_px * 2.5, 0.0))

        queue = deque(roots)
        while queue:
            u = queue.popleft()
            if u in placed:
                continue
            if any(p not in placed for p in in_adj[u]):
                queue.append(u)     # re-enqueue until all parents are done
                continue

            sx, sy = NetworkDrawer._averageSuggestions(suggestions[u])
            placed[u] = (sx, sy)

            for d in out_adj[u]:
                if d in placed:
                    continue
                dx, dy = NetworkDrawer._worldDirection(nodes, by_str, u, d)
                suggestions[d].append((sx + edge_px * dx, sy + edge_px * dy))

                in_degree[d] -= 1
                if in_degree[d] == 0:
                    queue.append(d)

        NetworkDrawer._placeUnvisited(nodes, by_str, placed, all_str, edge_px)
        NetworkDrawer._writePlacements(nodes, by_str, placed)

    # ------------------------------------------------------------------
    # Fixed-length layout helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _buildAdjacency(conduits, by_str):
        """Return (out_adj, in_adj) dicts built from the conduit list."""
        out_adj = defaultdict(list)
        in_adj  = defaultdict(list)
        for c in (conduits or []):
            u = str(c.get("upstream",   "")).strip()
            d = str(c.get("downstream", "")).strip()
            if u in by_str and d in by_str and u != d:
                out_adj[u].append(d)
                in_adj[d].append(u)
        return out_adj, in_adj

    @staticmethod
    def _averageSuggestions(suggestions):
        """Return the centroid of a list of (x, y) suggestions."""
        sx = sum(s[0] for s in suggestions) / len(suggestions)
        sy = sum(s[1] for s in suggestions) / len(suggestions)
        return sx, sy

    @staticmethod
    def _worldDirection(nodes, by_str, u, d):
        """
        Return the unit vector pointing from node u to node d in world space.
        Falls back to (1, 0) when both nodes share the same position.
        """
        u_data = nodes[by_str[u]]
        d_data = nodes[by_str[d]]
        wdx = d_data["x"] - u_data["x"]
        wdy = d_data["y"] - u_data["y"]
        wdist = math.sqrt(wdx * wdx + wdy * wdy)
        if wdist < 1e-6:
            return 1.0, 0.0
        return wdx / wdist, wdy / wdist

    @staticmethod
    def _placeUnvisited(nodes, by_str, placed, all_str, edge_px):
        """Place any nodes not reached by the topological traversal (cycles / islands)."""
        unplaced = all_str - set(placed)
        if unplaced:
            max_y = max((placed[n][1] for n in placed), default=0)
            for i, nid in enumerate(sorted(unplaced)):
                placed[nid] = (i * edge_px, max_y + edge_px * 2)

    @staticmethod
    def _writePlacements(nodes, by_str, placed):
        """Copy computed (x, y) positions back into the nodes dict."""
        for sid, (x, y) in placed.items():
            nodes[by_str[sid]]["x"] = x
            nodes[by_str[sid]]["y"] = y

    # ------------------------------------------------------------------
    # Segment flattening
    # ------------------------------------------------------------------

    @staticmethod
    def _flattenAlignedSegments(nodes, conduits, angle_threshold_deg=15.0):
        """
        For every conduit whose two endpoints are nearly horizontal or nearly
        vertical (within angle_threshold_deg of the axis), snap both nodes so
        they share the exact same y- (horizontal) or x- (vertical) coordinate.

        Uses the average of the two coordinates so neither node is forced to
        move more than the other. Runs multiple passes so alignment propagates
        along chains: if A→B is horizontal and B→C is horizontal, all three
        end up on the same y after two passes.
        """
        if not nodes or not conduits:
            return

        by_str = {str(nid): nid for nid in nodes}
        threshold = math.sin(math.radians(angle_threshold_deg))

        # Multiple passes let alignment propagate along chains
        for _ in range(5):
            changed = False
            for c in conduits:
                u_str = str(c.get("upstream",   "")).strip()
                d_str = str(c.get("downstream", "")).strip()
                if u_str not in by_str or d_str not in by_str:
                    continue

                u_data = nodes[by_str[u_str]]
                d_data = nodes[by_str[d_str]]

                dx = d_data["x"] - u_data["x"]
                dy = d_data["y"] - u_data["y"]
                length = math.sqrt(dx * dx + dy * dy)
                if length < 1e-6:
                    continue

                if abs(dy) / length < threshold:          # nearly horizontal
                    avg_y = (u_data["y"] + d_data["y"]) / 2.0
                    if u_data["y"] != avg_y or d_data["y"] != avg_y:
                        u_data["y"] = avg_y
                        d_data["y"] = avg_y
                        changed = True
                elif abs(dx) / length < threshold:        # nearly vertical
                    avg_x = (u_data["x"] + d_data["x"]) / 2.0
                    if u_data["x"] != avg_x or d_data["x"] != avg_x:
                        u_data["x"] = avg_x
                        d_data["x"] = avg_x
                        changed = True

            if not changed:
                break

    # ------------------------------------------------------------------
    # Overlap removal
    # ------------------------------------------------------------------

    @staticmethod
    def _removeOverlaps(nodes, min_sep=60.0, max_iterations=200):
        """
        Iteratively push every overlapping pair apart until all nodes are at
        least min_sep pixels from each other, or max_iterations is reached.
        """
        nids = list(nodes.keys())
        n    = len(nids)
        if n < 2:
            return

        for _ in range(max_iterations):
            any_moved = False
            for i in range(n):
                for j in range(i + 1, n):
                    any_moved |= NetworkDrawer._separatePair(nodes, nids, i, j, n, min_sep)
            if not any_moved:
                break

    @staticmethod
    def _separatePair(nodes, nids, i, j, n, min_sep):
        """Push nodes i and j apart if they are closer than min_sep. Returns True if moved."""
        a, b = nids[i], nids[j]
        dx = nodes[b]["x"] - nodes[a]["x"]
        dy = nodes[b]["y"] - nodes[a]["y"]
        dist = math.sqrt(dx * dx + dy * dy)

        if dist >= min_sep:
            return False

        if dist < 1e-6:
            angle    = 2 * math.pi * j / n
            dx, dy, dist = math.cos(angle), math.sin(angle), 1.0

        push = (min_sep - dist) / 2.0
        ux, uy = dx / dist, dy / dist
        nodes[a]["x"] -= ux * push
        nodes[a]["y"] -= uy * push
        nodes[b]["x"] += ux * push
        nodes[b]["y"] += uy * push
        return True

    # ------------------------------------------------------------------
    # Scene construction
    # ------------------------------------------------------------------

    @staticmethod
    def _buildNodeItems(scene, nodes, monitors, inserted_manholes=None):
        """
        Create an SVG item for every node, add it to the scene, and return
        two lookup dicts: one keyed by original node_id, one by str(node_id).
        """
        node_items     = {}
        node_items_str = {}

        for node_id, data in nodes.items():
            node_type    = NetworkDrawer._resolveNodeType(node_id, data, monitors, inserted_manholes)
            x            = data.get("x", 0.0)
            y            = -data.get("y", 0.0)      # flip y: world ↑ → screen ↓
            tooltip_text = data.get("tooltip")

            item = SvgNodeFactory.create(node_id, node_type, x, y, tooltip_text=tooltip_text)
            scene.addItem(item)
            node_items[node_id]          = item
            node_items_str[str(node_id)] = item

        return node_items, node_items_str

    @staticmethod
    def _resolveNodeType(node_id, data, monitors, inserted_manholes=None):
        """
        Return the display type for a node.

        Manholes that appear in the monitors dict are shown as 'flowmonitor',
        unless they were already replaced by a dedicated monitor node
        (replaced manholes are absent from `nodes` entirely, so this branch
        is only reached for manholes whose monitorInformation had no valid link).
        """
        node_type = data["type"]
        if monitors and node_id in monitors:
            already_replaced = inserted_manholes and str(node_id) in inserted_manholes
            if not already_replaced:
                if isinstance(node_type, str) and node_type.strip().lower() == "manhole":
                    return "flowmonitor"
        return node_type

    @staticmethod
    def _buildPipeItems(scene, conduits, node_items_str):
        """Create a PipeItem for every conduit and register it on its endpoint nodes."""
        for c in (conduits or []):
            up      = str(c.get("upstream",   "")).strip()
            ds      = str(c.get("downstream", "")).strip()
            edge_id = c.get("id")
            ctype = str(c.get("type", "conduit")).strip().lower()
            print(f"[DRAW] Link: {edge_id} | Type: {ctype}")

            # Prefer an explicit per-link colour (hex string) if provided
            explicit = c.get("colour")
            if explicit:
                try:
                    colour = explicit if isinstance(explicit, QColor) else QColor(str(explicit))
                except Exception:
                    colour = CONDUIT_COLOURS.get(ctype, CONDUIT_COLOURS["conduit"])
            else:
                colour = CONDUIT_COLOURS.get(ctype, CONDUIT_COLOURS["conduit"])

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
                routing="straight",
            )
            scene.addItem(pipe)
            up_item.connectedPipes.append(pipe)
            ds_item.connectedPipes.append(pipe)

    # ------------------------------------------------------------------
    # Compression
    # ------------------------------------------------------------------

    @staticmethod
    def _compressToMonitors(conduits, nodes, monitors):
        """
        Collapse the full network down to only monitor nodes and non-manhole
        structures. Chains of plain manholes are replaced with a direct edge.
        Nodes with no path to or from any monitor are dropped entirely.
        Returns (compressed_conduits, compressed_nodes).
        """
        G          = NetworkDrawer._buildGraph(conduits)
        monitor_ids = {str(k) for k in (monitors or {})}
        important  = {n for n in G.nodes if NetworkDrawer._isImportant(n, nodes, monitor_ids)}

        compressed_conduits = NetworkDrawer._traceCompressedEdges(G, important, conduits)
        compressed_nodes    = NetworkDrawer._filterConnectedNodes(nodes, compressed_conduits)

        print(f"--- COMPRESSION: {len(nodes)} nodes → {len(compressed_nodes)}, "
              f"{len(conduits or [])} conduits → {len(compressed_conduits)} ---")

        return compressed_conduits, compressed_nodes

    @staticmethod
    def _isImportant(node_id, nodes, monitor_ids):
        """A node is important if it is a monitor or is not a plain manhole."""
        if str(node_id) in monitor_ids:
            return True
        data = nodes.get(node_id) or nodes.get(str(node_id), {})
        return str(data.get("type", "")).strip().lower() != "manhole"

    @staticmethod
    def _traceCompressedEdges(G, important, conduits):
        """
        BFS from each important node through manhole intermediates.
        Emits a direct edge whenever another important node is reached.
        If a direct original conduit exists between two important nodes, reuse its id/type/colour.
        """
        compressed = []
        seen_edges = set()

        # Map direct (up, ds) -> original conduit dict so we can preserve id/type/colour
        direct_edge = {}
        for c in (conduits or []):
            up = str(c.get("upstream", "")).strip()
            ds = str(c.get("downstream", "")).strip()
            if up and ds:
                # If duplicates exist, keep the first one encountered
                direct_edge.setdefault((up, ds), c)

        for start in important:
            visited  = {start}
            frontier = list(G.successors(start))

            while frontier:
                next_frontier = []
                for node in frontier:
                    if node in visited:
                        continue
                    visited.add(node)
                    if node in important:
                        key = (start, node)
                        if key not in seen_edges:
                            seen_edges.add(key)
                            original = direct_edge.get((start, node))
                            if original is not None:
                                compressed.append({
                                    "id":         original.get("id"),
                                    "upstream":   start,
                                    "downstream": node,
                                    "type":       original.get("type", "conduit"),
                                    "colour":     original.get("colour"),
                                })
                            else:
                                compressed.append({
                                    "id":         f"{start}_to_{node}",
                                    "upstream":   start,
                                    "downstream": node,
                                    "type":       "conduit",
                                })
                    else:
                        next_frontier.extend(G.successors(node))
                frontier = next_frontier

        return compressed

    @staticmethod
    def _filterConnectedNodes(nodes, compressed_conduits):
        """Keep only nodes that appear in at least one compressed edge."""
        edge_node_ids = set()
        for c in compressed_conduits:
            edge_node_ids.add(c["upstream"])
            edge_node_ids.add(c["downstream"])

        return {
            nid: data for nid, data in nodes.items()
            if str(nid) in edge_node_ids or nid in edge_node_ids
        }
