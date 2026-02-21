from PyQt6.QtWidgets import QGraphicsScene, QGraphicsView
from PyQt6.QtGui import QPen, QPainterPath
from PyQt6.QtCore import Qt, QPointF
from Shapes import RectangleNode, OvalNode, TriangleNode
from Shapes import *
from PyQt6.QtSvgWidgets import QGraphicsSvgItem
from SvgNodeFactory import SvgNodeFactory


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
        scene = QGraphicsScene()

        # Draw nodes
        for node_id, data in nodes.items():
            node_type = data["type"]
            x = data["x"]
            y = -data["y"]  # flip y for Qt coordinate system

            item = SvgNodeFactory.create(node_type, x, y)
            scene.addItem(item)

        # Create and return view
        view = QGraphicsView(scene)
        return view