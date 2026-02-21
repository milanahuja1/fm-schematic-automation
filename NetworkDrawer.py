from PyQt6.QtWidgets import QGraphicsScene, QGraphicsView
from PyQt6.QtGui import QPen, QPainterPath
from PyQt6.QtCore import Qt, QPointF
from Shapes import RectangleNode, OvalNode, TriangleNode
from Shapes import *
from PyQt6.QtSvgWidgets import QGraphicsSvgItem


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
        view = QGraphicsView(scene)

        item = QGraphicsSvgItem("shapes/node.svg")
        scene.addItem(item)

        item = QGraphicsSvgItem("shapes/redtriangle.svg")
        scene.addItem(item)

        item = QGraphicsSvgItem("shapes/greenoval.svg")
        scene.addItem(item)
        return view