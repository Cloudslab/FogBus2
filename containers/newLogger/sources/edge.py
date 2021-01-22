class Edge:

    def __init__(
            self,
            source: str,
            destination: str,
            averagePackageSize: float = None,
            averageRoundTripDelay: float = None,

    ):
        self.source: str = source
        self.destination: str = destination
        self.averageReceivedPackageSize: float = averagePackageSize
        self.averageRoundTripDelay: float = averageRoundTripDelay
