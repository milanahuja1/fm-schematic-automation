import math
from PyQt6.QtWidgets import QGraphicsItem, QToolTip
from PyQt6.QtGui import QPen, QBrush, QPainterPath, QPolygonF, QColor
from PyQt6.QtCore import Qt, QRectF, QPointF, QPoint


class PipeItem(QGraphicsItem):
    """A hoverable directed pipe drawn as a straight line + arrowhead.

    This item stores references to two node QGraphicsItems. Call `updatePosition()`
    whenever either node moves.

    The pipe endpoints are computed from each node's sceneBoundingRect().center().
    """

    def __init__(
        self,
        upstream_item: QGraphicsItem,
        downstream_item: QGraphicsItem,
        edge_id=None,
        pen_colour=None,
        base_width: int = 1,
        hover_width: int = 2,
        arrow_size: float = 10.0,
        hit_width: float = 12.0,
        draw_label: bool = False,
        routing: str = "straight",
    ):
        super().__init__()

        self.upstream_item = upstream_item
        self.downstream_item = downstream_item
        self.edge_id = edge_id
        self.pen_colour = pen_colour

        self.base_width = int(base_width)
        self.hover_width = int(hover_width)
        self.arrow_size = float(arrow_size)
        self.hit_width = float(hit_width)
        self.draw_label = bool(draw_label)
        self.routing = routing  # "straight" or "orthogonal"

        self._hover = False

        self.setAcceptHoverEvents(True)
        self.setZValue(-10)  # keep pipes behind nodes

        # geometry caches
        self._draw_path = QPainterPath()
        self._arrow_poly = QPolygonF()
        self._hit_shape = QPainterPath()
        self._bounds = QRectF()
        self._label_pos = None

        self.updatePosition()

    # -----------------
    # Qt required API
    # -----------------

    def boundingRect(self) -> QRectF:
        return self._bounds

    def shape(self) -> QPainterPath:
        return self._hit_shape

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(painter.RenderHint.Antialiasing, True)

        colour = self.pen_colour
        if isinstance(colour, str):
            colour = QColor(colour)

        if colour is None:
            pen = QPen(Qt.GlobalColor.black)
            brush = QBrush(Qt.GlobalColor.black)
        else:
            pen = QPen(colour)
            brush = QBrush(colour)

        pen.setWidth(self.hover_width if self._hover else self.base_width)
        pen.setCosmetic(True)
        painter.setPen(pen)

        painter.drawPath(self._draw_path)

        painter.setBrush(brush)
        painter.drawPolygon(self._arrow_poly)

        if self.draw_label and self.edge_id is not None and self._label_pos is not None:
            painter.setPen(pen)
            painter.drawText(self._label_pos, str(self.edge_id))

    # -----------------
    # Hover behaviour
    # -----------------

    def hoverEnterEvent(self, event):
        self._hover = True
        self.update()

        u_id = getattr(self.upstream_item, "node_id", None)
        d_id = getattr(self.downstream_item, "node_id", None)

        lines = []
        if self.edge_id is not None:
            lines.append(f"Pipe: {self.edge_id}")
        if u_id is not None and d_id is not None:
            lines.append(f"{u_id} -> {d_id}")

        text = "\n".join(lines) if lines else "Pipe"

        pos = event.screenPos()
        if hasattr(pos, "toPoint"):
            pos = pos.toPoint()
        else:
            pos = QPoint(int(pos.x()), int(pos.y()))

        QToolTip.showText(pos + QPoint(6, 6), text)
        super().hoverEnterEvent(event)

    def hoverMoveEvent(self, event):
        u_id = getattr(self.upstream_item, "node_id", None)
        d_id = getattr(self.downstream_item, "node_id", None)

        lines = []
        if self.edge_id is not None:
            lines.append(f"Pipe: {self.edge_id}")
        if u_id is not None and d_id is not None:
            lines.append(f"{u_id} -> {d_id}")

        text = "\n".join(lines) if lines else "Pipe"

        pos = event.screenPos()
        if hasattr(pos, "toPoint"):
            pos = pos.toPoint()
        else:
            pos = QPoint(int(pos.x()), int(pos.y()))

        QToolTip.showText(pos + QPoint(6, 6), text)
        super().hoverMoveEvent(event)

    def hoverLeaveEvent(self, event):
        self._hover = False
        self.update()
        QToolTip.hideText()
        super().hoverLeaveEvent(event)

    # -----------------
    # Public API
    # -----------------

    def updatePosition(self):
        """Recompute endpoints/arrow/bounds based on current node positions."""
        if self.upstream_item is None or self.downstream_item is None:
            return

        # Endpoints are in scene coordinates
        start = self.upstream_item.sceneBoundingRect().center()
        end = self.downstream_item.sceneBoundingRect().center()

        self.prepareGeometryChange()

        x1, y1 = start.x(), start.y()
        x2, y2 = end.x(), end.y()
        dx = x2 - x1
        dy = y2 - y1
        a = self.arrow_size

        if self.routing == "orthogonal" and not (abs(dx) < 1e-3 and abs(dy) < 1e-3):
            # Route as an L-shape. Choose elbow direction based on dominant axis.
            # Horizontal-first: go to (x2, y1) then (x2, y2).
            # Vertical-first:   go to (x1, y2) then (x2, y2).
            # Use horizontal-first when the pipe is wider than it is tall.
            if abs(dx) >= abs(dy):
                elbow = QPointF(x2, y1)   # horizontal-first
            else:
                elbow = QPointF(x1, y2)   # vertical-first

            path = QPainterPath(QPointF(x1, y1))
            path.lineTo(elbow)
            path.lineTo(QPointF(x2, y2))
            self._draw_path = path

            # Arrow on the final segment, at its midpoint
            seg_dx = x2 - elbow.x()
            seg_dy = y2 - elbow.y()
            angle = math.atan2(seg_dy, seg_dx) if not (seg_dx == 0 and seg_dy == 0) else 0.0
            tip_x = (elbow.x() + x2) / 2.0
            tip_y = (elbow.y() + y2) / 2.0

            # Hit shape: two rectangles covering each leg
            hit = QPainterPath()
            hw = self.hit_width / 2.0
            # Leg 1: start → elbow
            lx1, ly1, lx2, ly2 = x1, y1, elbow.x(), elbow.y()
            if abs(lx2 - lx1) >= abs(ly2 - ly1):
                hit.addRect(QRectF(min(lx1, lx2), ly1 - hw, abs(lx2 - lx1), 2 * hw))
            else:
                hit.addRect(QRectF(lx1 - hw, min(ly1, ly2), 2 * hw, abs(ly2 - ly1)))
            # Leg 2: elbow → end
            lx1, ly1, lx2, ly2 = elbow.x(), elbow.y(), x2, y2
            if abs(lx2 - lx1) >= abs(ly2 - ly1):
                hit.addRect(QRectF(min(lx1, lx2), ly1 - hw, abs(lx2 - lx1), 2 * hw))
            else:
                hit.addRect(QRectF(lx1 - hw, min(ly1, ly2), 2 * hw, abs(ly2 - ly1)))

            # Label near the elbow
            mid = elbow
        else:
            # Straight line (default)
            path = QPainterPath(QPointF(x1, y1))
            path.lineTo(QPointF(x2, y2))
            self._draw_path = path

            angle = math.atan2(dy, dx) if not (dx == 0 and dy == 0) else 0.0
            tip_x = x1 + 0.5 * dx
            tip_y = y1 + 0.5 * dy

            hit = QPainterPath()
            hw = self.hit_width / 2.0
            if not (x1 == x2 and y1 == y2):
                if abs(dx) >= abs(dy):
                    hit.addRect(QRectF(min(x1, x2), y1 - hw, abs(dx), 2 * hw))
                else:
                    hit.addRect(QRectF(x1 - hw, min(y1, y2), 2 * hw, abs(dy)))

            mid = QPointF((x1 + x2) / 2.0, (y1 + y2) / 2.0)

        # Arrowhead
        p1 = QPointF(tip_x, tip_y)
        p2 = QPointF(
            tip_x - a * math.cos(angle - math.pi / 6.0),
            tip_y - a * math.sin(angle - math.pi / 6.0),
        )
        p3 = QPointF(
            tip_x - a * math.cos(angle + math.pi / 6.0),
            tip_y - a * math.sin(angle + math.pi / 6.0),
        )
        self._arrow_poly = QPolygonF([p1, p2, p3])

        hit.addPolygon(self._arrow_poly)
        self._hit_shape = hit

        # Label
        self._label_pos = QPointF(mid.x() + 4.0, mid.y() - 6.0)

        # Bounds
        rect = self._draw_path.boundingRect().united(self._arrow_poly.boundingRect())
        pad = max(self.hit_width, self.arrow_size) + 2.0
        self._bounds = QRectF(rect.left() - pad, rect.top() - pad, rect.width() + 2 * pad, rect.height() + 2 * pad)

        self.update()