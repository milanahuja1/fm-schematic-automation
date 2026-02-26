import os
from PyQt6.QtSvgWidgets import QGraphicsSvgItem
from PyQt6.QtWidgets import QGraphicsSimpleTextItem
from PyQt6.QtGui import QFont, QGuiApplication, QPalette
from PyQt6.QtCore import QPointF


class SvgNodeItem(QGraphicsSvgItem):
    GRID_SIZE = 25  # scene units

    def __init__(self, path, node_id, node_type, tooltip_text=None):
        super().__init__(path)
        self.node_id = node_id
        self.node_type = node_type
        self.base_scale = 1.0
        self.setFlag(self.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(self.GraphicsItemFlag.ItemIsSelectable, True)
        self.connectedPipes = []
        self.setFlag(self.GraphicsItemFlag.ItemSendsGeometryChanges, True)

        self.setAcceptHoverEvents(True)
        #self.setTransformOriginPoint(self.boundingRect().center())
        self.setToolTip(tooltip_text or f"Node: {node_id}\nType: {node_type}")

    def hoverEnterEvent(self, event):
        #self.setScale(self.base_scale * 1.1)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        #self.setScale(self.base_scale)
        super().hoverLeaveEvent(event)


    def itemChange(self, change, value):
        # Snap to grid while dragging
        if change == self.GraphicsItemChange.ItemPositionChange and isinstance(value, QPointF):
            g = float(self.GRID_SIZE)
            if g > 0:
                x = round(value.x() / g) * g
                y = round(value.y() / g) * g
                return QPointF(x, y)

        # When this node moves, update any connected pipes
        if change == self.GraphicsItemChange.ItemPositionHasChanged:
            for pipe in self.connectedPipes:
                pipe.updatePosition()

        return super().itemChange(change, value)


class SvgNodeFactory:
    # Map node "type" values to SVG filenames
    SVG_MAP = {

        "manhole": "manhole.svg",
        "flowmonitor": "flowMonitor.svg",
        "weir": "weir.svg",
        "outfall": "outfall.svg",
        "storage": "storage.svg",
    }

    # folder containing the SVG files
    SVG_DIR = os.path.join("shapes")

    @staticmethod
    def create(node_id, node_type, x, y, width=50, tooltip_text=None):
        key = node_type
        if isinstance(key, str):
            key = key.strip().lower()
        else:
            # keep ints as-is; attempt to coerce numeric strings handled above
            try:
                key = int(key)
            except Exception:
                pass

        svg_file = SvgNodeFactory.SVG_MAP.get(key)
        if svg_file is None:
            # Fallback to manhole symbol if unknown
            svg_file = SvgNodeFactory.SVG_MAP.get("manhole", "flowMonitor.svg")

        path = os.path.join(SvgNodeFactory.SVG_DIR, svg_file)
        item = SvgNodeItem(path, node_id=node_id, node_type=node_type, tooltip_text=tooltip_text)

        bounds = item.renderer().viewBoxF()
        scale = 1.0 if bounds.width() == 0 else (float(width) / bounds.width())
        item.setScale(scale)
        item.base_scale = scale

        # --------------------------
        # Attach ID label under symbol (child of SVG)
        # --------------------------
        label = QGraphicsSimpleTextItem(str(node_id), item)
        label.setFlag(label.GraphicsItemFlag.ItemIgnoresTransformations, True)

        font = QFont("Fira Code", 12)
        font.setBold(True)
        label.setFont(font)

        # Theme-aware label colour (follows OS light/dark mode)
        try:
            label_colour = QGuiApplication.palette().color(QPalette.ColorRole.WindowText)
            label.setBrush(label_colour)
        except Exception:
            pass

        # centre label horizontally under the SVG
        svg_bounds = item.boundingRect()
        text_bounds = label.boundingRect()

        label.setPos(
            svg_bounds.width() / 2.0 - text_bounds.width() / 2.0,
            svg_bounds.height() + 4.0,
        )

        # centre the SVG at (x, y)
        item.setPos(
            float(x) - (bounds.width() * scale) / 2.0,
            float(y) - (bounds.height() * scale) / 2.0,
        )

        return item