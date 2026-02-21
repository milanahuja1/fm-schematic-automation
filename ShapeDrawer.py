import turtle
import math

class ShapeDrawer:
    # ---------- Layout ----------
    @staticmethod
    def circle_layout(nodes, centre=(0, 0), radius=220):
        nodes = sorted(nodes, key=str)
        n = len(nodes)
        cx, cy = centre
        pos = {}

        for i, node in enumerate(nodes):
            angle = 2 * math.pi * i / max(n, 1)
            x = cx + radius * math.cos(angle)
            y = cy + radius * math.sin(angle)
            pos[node] = (x, y)

        return pos

    @staticmethod
    def normalise_positions(positions):
        """
        Recentre a positions dict so the drawing is centred on screen.
        positions: { node_id: (x, y) }
        """
        xs = [p[0] for p in positions.values()]
        ys = [p[1] for p in positions.values()]
        cx = (min(xs) + max(xs)) / 2.0
        cy = (min(ys) + max(ys)) / 2.0

        out = {}
        for k, (x, y) in positions.items():
            out[k] = (x - cx, y - cy)
        return out


    @staticmethod
    def draw_pipe_with_arrow(t, x1, y1, x2, y2, elbow="mid"):
        """
        Draw an orthogonal (right-angle) pipe from (x1,y1) to (x2,y2),
        with an arrow head at the end indicating direction.
        elbow:
            "mid" -> go to mid-x, then vertical, then horizontal
            "hvh" -> horizontal then vertical
            "vhv" -> vertical then horizontal
        """
        if elbow == "vhv":
            px, py = x1, y2
            path = [(x1, y1), (px, py), (x2, y2)]
        elif elbow == "hvh":
            px, py = x2, y1
            path = [(x1, y1), (px, py), (x2, y2)]
        else:
            mx = (x1 + x2) / 2.0
            path = [(x1, y1), (mx, y1), (mx, y2), (x2, y2)]

        # draw the polyline
        t.penup()
        t.goto(path[0][0], path[0][1])
        t.pendown()
        for (px, py) in path[1:]:
            t.goto(px, py)

        # arrow head aligned with the final segment direction
        (ax0, ay0) = path[-2]
        (ax1, ay1) = path[-1]
        ShapeDrawer.draw_arrow(t, ax0, ay0, ax1, ay1)

    # ---------- Drawing primitives ----------
    @staticmethod
    def draw_rect(t, cx, cy, w, h, pen_colour="black", fill_colour=None):
        t.penup()
        t.goto(cx - w / 2, cy - h / 2)
        t.pendown()
        t.pencolor(pen_colour)

        if fill_colour is not None:
            t.fillcolor(fill_colour)
            t.begin_fill()

        t.setheading(0)
        for _ in range(2):
            t.forward(w)
            t.left(90)
            t.forward(h)
            t.left(90)

        if fill_colour is not None:
            t.end_fill()

    @staticmethod
    def draw_triangle(t, cx, cy, size, pen_colour="black", fill_colour=None):
        """
        Draw an upright equilateral triangle centred roughly at (cx, cy).
        size is the side length.
        """
        h = (math.sqrt(3) / 2.0) * size

        # Start at bottom-left corner
        x0 = cx - size / 2.0
        y0 = cy - h / 3.0

        t.penup()
        t.goto(x0, y0)
        t.pendown()
        t.pencolor(pen_colour)

        if fill_colour is not None:
            t.fillcolor(fill_colour)
            t.begin_fill()

        t.setheading(0)
        t.forward(size)
        t.left(120)
        t.forward(size)
        t.left(120)
        t.forward(size)

        if fill_colour is not None:
            t.end_fill()

    @staticmethod
    def draw_oval_horizontal(t, cx, cy, width, height, pen_colour="black", fill_colour=None, steps=120):
        """
        Draw a horizontal oval (ellipse) centred at (cx, cy) with bounding box width x height.
        """
        if width <= 0 or height <= 0:
            return

        a = width / 2.0
        b = height / 2.0

        t.pencolor(pen_colour)
        if fill_colour is not None:
            t.fillcolor(fill_colour)
            t.begin_fill()

        # Start on the right-most point
        t.penup()
        t.goto(cx + a, cy)
        t.pendown()

        for i in range(steps + 1):
            theta = 2.0 * math.pi * (i / steps)
            x = cx + a * math.cos(theta)
            y = cy + b * math.sin(theta)
            t.goto(x, y)

        if fill_colour is not None:
            t.end_fill()

    @staticmethod
    def write_text(t, x, y, text, align="center", font=("Arial", 10, "normal")):
        t.penup()
        t.goto(x, y)
        t.pendown()
        t.write(str(text), align=align, font=font)

    @staticmethod
    def draw_arrow(t, x1, y1, x2, y2, head_len=12, head_angle_deg=25):
        # Draw the shaft
        t.penup()
        t.goto(x1, y1)
        t.pendown()
        t.goto(x2, y2)

        # Draw a filled triangular arrow head at (x2, y2)
        angle = math.atan2(y2 - y1, x2 - x1)
        left = angle + math.radians(180 - head_angle_deg)
        right = angle - math.radians(180 - head_angle_deg)

        lx = x2 + head_len * math.cos(left)
        ly = y2 + head_len * math.sin(left)
        rx = x2 + head_len * math.cos(right)
        ry = y2 + head_len * math.sin(right)

        t.begin_fill()
        t.penup()
        t.goto(x2, y2)
        t.pendown()
        t.goto(lx, ly)
        t.goto(rx, ry)
        t.goto(x2, y2)
        t.end_fill()

    # ---------- Arrow clipping helpers ----------
    @staticmethod
    def _clip_to_rect_boundary(cx, cy, w, h, x_from, y_from, x_to, y_to):
        """
        Returns the point where the ray from (x_from, y_from) toward (x_to, y_to)
        intersects the rectangle centred at (cx, cy) with width w and height h.
        If the line is degenerate, returns the centre.
        """
        dx = x_to - x_from
        dy = y_to - y_from
        if dx == 0 and dy == 0:
            return cx, cy

        half_w = w / 2.0
        half_h = h / 2.0

        t_candidates = []

        # Vertical sides: x = cx +/- half_w
        if dx != 0:
            t1 = (cx + half_w - cx) / dx
            y1 = cy + t1 * dy
            if t1 > 0 and (cy - half_h) <= y1 <= (cy + half_h):
                t_candidates.append(t1)

            t2 = (cx - half_w - cx) / dx
            y2 = cy + t2 * dy
            if t2 > 0 and (cy - half_h) <= y2 <= (cy + half_h):
                t_candidates.append(t2)

        # Horizontal sides: y = cy +/- half_h
        if dy != 0:
            t3 = (cy + half_h - cy) / dy
            x3 = cx + t3 * dx
            if t3 > 0 and (cx - half_w) <= x3 <= (cx + half_w):
                t_candidates.append(t3)

            t4 = (cy - half_h - cy) / dy
            x4 = cx + t4 * dx
            if t4 > 0 and (cx - half_w) <= x4 <= (cx + half_w):
                t_candidates.append(t4)

        if not t_candidates:
            return cx, cy

        t_min = min(t_candidates)
        return cx + t_min * dx, cy + t_min * dy

    @staticmethod
    def clipped_edge_points(src_pos, dst_pos, node_w, node_h):
        """
        Returns (sx, sy, ex, ey) so arrows start/end on rectangle boundaries
        rather than at the centres.
        """
        sx, sy = src_pos
        dx, dy = dst_pos

        start_x, start_y = ShapeDrawer._clip_to_rect_boundary(sx, sy, node_w, node_h, sx, sy, dx, dy)
        end_x, end_y = ShapeDrawer._clip_to_rect_boundary(dx, dy, node_w, node_h, dx, dy, sx, sy)

        return start_x, start_y, end_x, end_y

    # ---------- Graph drawing ----------
    @staticmethod
    def draw_graph(graph, node_types=None, node_positions=None, node_w=70, node_h=40, title="Map"):
        """
        graph format:
            { upstream: [(downstream, edge_id), ...], ... }
        """
        # collect nodes from sources + targets
        nodes = set(graph.keys())
        for src, outs in graph.items():
            for (dst, edge_id) in outs:
                nodes.add(dst)

        # also include any nodes that only appear in the node table
        if node_types is not None:
            for nid in node_types.keys():
                nodes.add(nid)

        if node_positions is None:
            positions = ShapeDrawer.circle_layout(nodes)
        else:
            # Use provided x,y positions to make it look schematic/map-like
            positions = ShapeDrawer.normalise_positions(node_positions)

        screen = turtle.Screen()
        screen.title(title)
        screen.tracer(0, 0)  # fast draw

        t = turtle.Turtle()
        t.hideturtle()
        t.speed(0)
        t.pensize(2)

        # draw edges first (so nodes sit on top)
        for src, outs in graph.items():
            x1, y1 = positions[src]
            for (dst, edge_id) in outs:
                x2, y2 = positions[dst]

                t.pencolor("black")
                t.fillcolor("black")
                sx, sy, ex, ey = ShapeDrawer.clipped_edge_points((x1, y1), (x2, y2), node_w, node_h)
                if node_positions is None:
                    ShapeDrawer.draw_arrow(t, sx, sy, ex, ey)
                else:
                    # orthogonal routing feels more like pipes on a map
                    ShapeDrawer.draw_pipe_with_arrow(t, sx, sy, ex, ey, elbow="mid")

                # edge id box at midpoint (centre-to-centre midpoint for readability)
                mx = (x1 + x2) / 2
                my = (y1 + y2) / 2
                ShapeDrawer.draw_rect(t, mx, my, 46, 22, pen_colour="black", fill_colour="white")
                t.pencolor("black")
                ShapeDrawer.write_text(t, mx, my - 6, edge_id, font=("Arial", 9, "normal"))

        # draw nodes
        for node, (x, y) in positions.items():
            node_type = None
            if node_types is not None and node in node_types:
                node_type = node_types[node]

            # type 1: rectangle
            if node_type == 1 or node_type is None:
                ShapeDrawer.draw_rect(t, x, y, node_w, node_h, pen_colour="black", fill_colour="#f2f2f2")

            # type 2: green horizontal oval
            elif node_type == 2:
                ShapeDrawer.draw_oval_horizontal(t, x, y, node_w, node_h, pen_colour="black", fill_colour="green")

            # type 3: red triangle
            elif node_type == 3:
                # use the smaller of width/height so it fits nicely
                side = min(node_w, node_h) * 1.15
                ShapeDrawer.draw_triangle(t, x, y, side, pen_colour="black", fill_colour="red")

            else:
                # unknown type, fall back to rectangle
                ShapeDrawer.draw_rect(t, x, y, node_w, node_h, pen_colour="black", fill_colour="#f2f2f2")

            t.pencolor("black")
            ShapeDrawer.write_text(t, x, y - 7, node, font=("Arial", 11, "normal"))

        screen.update()
        screen.mainloop()