import math
from PyQt6.QtWidgets import QGraphicsItem, QToolTip
from PyQt6.QtGui import QPen, QBrush, QPainterPath, QPolygonF
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
        base_width: int = 1,
        hover_width: int = 2,
        arrow_size: float = 10.0,
        hit_width: float = 12.0,
        draw_label: bool = False,
    ):
        super().__init__()

        self.upstream_item = upstream_item
        self.downstream_item = downstream_item
        self.edge_id = edge_id

        self.base_width = int(base_width)
        self.hover_width = int(hover_width)
        self.arrow_size = float(arrow_size)
        self.hit_width = float(hit_width)
        self.draw_label = bool(draw_label)

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

        pen = QPen(Qt.GlobalColor.black)
        pen.setWidth(self.hover_width if self._hover else self.base_width)
        pen.setCosmetic(True)
        painter.setPen(pen)

        painter.drawPath(self._draw_path)

        painter.setBrush(QBrush(Qt.GlobalColor.black))
        painter.drawPolygon(self._arrow_poly)

        if self.draw_label and self.edge_id is not None and self._label_pos is not None:
            painter.setPen(Qt.GlobalColor.black)
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

        # Draw path (straight)
        path = QPainterPath(QPointF(start.x(), start.y()))
        path.lineTo(QPointF(end.x(), end.y()))
        self._draw_path = path

        # Arrowhead from last segment direction
        dx = end.x() - start.x()
        dy = end.y() - start.y()
        angle = math.atan2(dy, dx) if not (dx == 0 and dy == 0) else 0.0

        # Arrowhead placed mid-line, pointing from upstream -> downstream
        a = self.arrow_size

        t = 0.5  # 0.5 = centre; push towards downstream (e.g. 0.6) if you prefer
        tip_x = start.x() + t * (end.x() - start.x())
        tip_y = start.y() + t * (end.y() - start.y())

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

        # Label near midpoint
        mid = QPointF((start.x() + end.x()) / 2.0, (start.y() + end.y()) / 2.0)
        self._label_pos = QPointF(mid.x() + 4.0, mid.y() - 6.0)

        # Bounds (expanded)
        rect = self._draw_path.boundingRect().united(self._arrow_poly.boundingRect())
        pad = max(self.hit_width, self.arrow_size) + 2.0
        self._bounds = QRectF(rect.left() - pad, rect.top() - pad, rect.width() + 2 * pad, rect.height() + 2 * pad)

        # Hit shape: a thick rectangle along the line + arrowhead
        hit = QPainterPath()
        hw = self.hit_width / 2.0

        x1, y1 = start.x(), start.y()
        x2, y2 = end.x(), end.y()

        if not (x1 == x2 and y1 == y2):
            if abs(x2 - x1) >= abs(y2 - y1):
                left = min(x1, x2)
                right = max(x1, x2)
                # approximate line hitbox as horizontal strip at y1
                hit.addRect(QRectF(left, y1 - hw, right - left, 2 * hw))
            else:
                top = min(y1, y2)
                bottom = max(y1, y2)
                hit.addRect(QRectF(x1 - hw, top, 2 * hw, bottom - top))

        hit.addPolygon(self._arrow_poly)
        self._hit_shape = hit

        self.update()