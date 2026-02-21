

from PyQt6.QtWidgets import QGraphicsRectItem, QGraphicsEllipseItem, QGraphicsPolygonItem
from PyQt6.QtGui import QBrush, QPen, QPolygonF
from PyQt6.QtCore import Qt, QPointF
import math


class BaseNode:
    """
    Base wrapper class for common node properties.
    """
    def __init__(self, node_id, x, y, width=70, height=40):
        self.node_id = node_id
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def center(self):
        return self.x, self.y


class RectangleNode(QGraphicsRectItem, BaseNode):
    def __init__(self, node_id, x, y, width=70, height=40):
        BaseNode.__init__(self, node_id, x, y, width, height)
        QGraphicsRectItem.__init__(
            self,
            x - width / 2,
            y - height / 2,
            width,
            height
        )

        self.setPen(QPen(Qt.GlobalColor.black, 2))
        self.setBrush(QBrush(Qt.GlobalColor.lightGray))


class OvalNode(QGraphicsEllipseItem, BaseNode):
    def __init__(self, node_id, x, y, width=70, height=40):
        BaseNode.__init__(self, node_id, x, y, width, height)
        QGraphicsEllipseItem.__init__(
            self,
            x - width / 2,
            y - height / 2,
            width,
            height
        )

        self.setPen(QPen(Qt.GlobalColor.black, 2))
        self.setBrush(QBrush(Qt.GlobalColor.green))


class TriangleNode(QGraphicsPolygonItem, BaseNode):
    def __init__(self, node_id, x, y, size=50):
        BaseNode.__init__(self, node_id, x, y, size, size)

        height = math.sqrt(3) / 2 * size

        p1 = QPointF(x, y - (2 / 3) * height)
        p2 = QPointF(x - size / 2, y + (1 / 3) * height)
        p3 = QPointF(x + size / 2, y + (1 / 3) * height)

        polygon = QPolygonF([p1, p2, p3])

        QGraphicsPolygonItem.__init__(self, polygon)

        self.setPen(QPen(Qt.GlobalColor.black, 2))
        self.setBrush(QBrush(Qt.GlobalColor.red))