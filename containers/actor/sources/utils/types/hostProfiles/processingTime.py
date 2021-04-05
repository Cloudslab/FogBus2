from typing import Dict

from .resources import Resources
from ..basic.autoDictionary import AutoDictionary
from ..basic.serializableDictionary import SerializableDictionary
from ...component.platformInfo import PlatformInfo


class ProcessingTime(AutoDictionary, SerializableDictionary):
    def __init__(
            self,
            taskExecutorName: str,
            processingTime: int = 0,
            resources: Resources = Resources(),
            platform: PlatformInfo = PlatformInfo()):
        self.taskExecutorName = taskExecutorName
        self.processingTime = processingTime
        self.resources = resources
        self.platform = platform

    @staticmethod
    def fromDict(inDict: Dict):
        processingTime = ProcessingTime(
            platform=PlatformInfo.fromDict(inDict['platform']),
            taskExecutorName=inDict['taskExecutorName'],
            processingTime=inDict['processingTime'],
            resources=Resources.fromDict(inDict['resources']))
        return processingTime

    def toDict(self) -> Dict:
        inDict = {
            'platform': self.platform.toDict(),
            'taskExecutorName': self.taskExecutorName,
            'processingTime': self.processingTime,
            'resources': self.resources.toDict()}
        return inDict
