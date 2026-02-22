class Pipe:
    def __init__(self, suffix, upstreamNode, downstreamNode):
        self.pipeID = upstreamNode + '.' + suffix
        self.upstreamNode = upstreamNode
        self.downstreamNode = downstreamNode

