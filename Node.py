class Node:
    def __init__(self, nodeID, x, y, nodeType=1, metadata=None):
        self.id = str(nodeID)
        self.x = float(x)
        self.y = float(y)
        self.type = int(nodeType)
        #extra info to show on hover (flow, pressure, name, etc.)
        self.metadata = metadata or {}
        #stores a list of tuples (nodeID, pipeID)
        self.downstream = list()
        self.upstream = list()
