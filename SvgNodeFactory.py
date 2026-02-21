import os
from PyQt6.QtSvgWidgets import QGraphicsSvgItem

class SvgNodeFactory:

    SVG_MAP = {
        1: "node.svg",
        2: "greenoval.svg",
        3: "redtriangle.svg",
    }

    SVG_DIR = os.path.join("shapes")

    @staticmethod
    def create(node_type, x, y, width=70):
        svg_file = SvgNodeFactory.SVG_MAP.get(node_type)

        if svg_file is None:
            raise ValueError(f"Unknown node type: {node_type}")

        path = os.path.join(SvgNodeFactory.SVG_DIR, svg_file)

        item = QGraphicsSvgItem(path)

        # ---- scale consistently ----
        renderer = item.renderer()
        bounds = renderer.viewBoxF()

        scale = width / bounds.width()
        item.setScale(scale)

        # ---- centre the item ----
        item.setPos(x - (bounds.width() * scale) / 2,
                    y - (bounds.height() * scale) / 2)

        return item