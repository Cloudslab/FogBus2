from typing import Dict

from .types import AllDataRate
from .types import AllDelay
from .types import AllLatency
from .types import AllPacketSize
from .types import AllProcessingTime
from .types import AllResponseTime
from ...types import AutoDictionary
from ...types import ProcessingTime
from ...types import SerializableDictionary


class AllSystemPerformance(AutoDictionary, SerializableDictionary):

    def __init__(
            self,
            dataRate: AllDataRate = None,
            delay: AllDelay = None,
            latency: AllLatency = None,
            packetSize: AllPacketSize = None,
            processingTime: AllProcessingTime = None,
            responseTime: AllResponseTime = None, ):
        self.dataRate: AllDataRate = \
            {} if dataRate is None else dataRate
        self.delay: AllDelay = \
            {} if delay is None else delay
        self.latency: AllLatency = \
            {} if latency is None else latency
        self.packetSize: AllPacketSize = \
            {} if packetSize is None else packetSize
        self.processingTime: AllProcessingTime = \
            {} if processingTime is None else processingTime
        self.responseTime: AllResponseTime = \
            {} if responseTime is None else responseTime

    @staticmethod
    def fromDict(inDict: Dict):
        processingTime = {}
        for key, processingTimeInDict in inDict['processingTime'].items():
            processingTime[key] = ProcessingTime.fromDict(processingTimeInDict)
        systemPerformance = AllSystemPerformance(
            processingTime=processingTime,
            responseTime=inDict['responseTime'],
            packetSize=inDict['packetSize'],
            delay=inDict['delay'],
            dataRate=inDict['dataRate'],
            latency=inDict['latency'])
        return systemPerformance

    def toDict(self) -> Dict:
        processingTimeInDict = {}
        for key, hostProcessingTime in self.processingTime.items():
            processingTimeInDict[key] = hostProcessingTime.toDict()

        inDict = {
            'processingTime': processingTimeInDict,
            'responseTime': self.responseTime,
            'packetSize': self.packetSize,
            'delay': self.delay,
            'dataRate': self.dataRate,
            'latency': self.latency}
        return inDict
