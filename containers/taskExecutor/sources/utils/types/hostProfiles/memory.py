from typing import Dict

from ..basic import AutoDictionary
from ..basic import SerializableDictionary


class Memory(AutoDictionary, SerializableDictionary):
    def __init__(
            self,
            maximum: int = 0,
            utilization: float = .0,
            utilizationPeak: float = .0, ):
        self.utilizationPeak = utilizationPeak
        self.utilization = utilization
        self.maximum = maximum

    def toDict(self):
        return dict(self)

    @staticmethod
    def fromDict(inDict: Dict):
        memory = Memory(
            maximum=inDict['maximum'],
            utilization=inDict['utilization'],
            utilizationPeak=inDict['utilizationPeak'])
        return memory
