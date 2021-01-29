from resourcesInfo import Dictionary


class Edge(Dictionary):

    def __init__(
            self,
            source: str = None,
            destination: str = None,
            averagePackageSize: float = None,
            averageRoundTripDelay: float = None,
            delay: float = None):
        self.source: str = source
        self.destination: str = destination
        self.averageReceivedPackageSize: float = averagePackageSize
        self.averageRoundTripDelay: float = averageRoundTripDelay
        self.delay: float = delay
        Dictionary.__init__(self)
