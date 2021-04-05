from typing import Dict

from ..basic import AutoDictionary


class CPU(AutoDictionary):
    def __init__(
            self,
            cores: int = 1,
            frequency: float = 2400.,
            utilization: float = .0,
            utilizationPeak: float = .0, ):
        self.cores = cores
        self.frequency = frequency
        self.utilization = utilization
        self.utilizationPeak = utilizationPeak

    def toDict(self):
        return dict(self)

    @staticmethod
    def fromDict(inDict: Dict):
        cpu = CPU(
            cores=inDict['cores'],
            frequency=inDict['frequency'],
            utilization=inDict['utilization'],
            utilizationPeak=inDict['utilizationPeak'])
        return cpu
