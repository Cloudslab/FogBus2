from typing import Dict

from .cpu import CPU
from .images import Images
from .memory import Memory
from .resources import Resources
from .runningContainres import RunningContainers
from ...component.platformInfo import PlatformInfo


class ActorResources(Resources):

    def __init__(
            self,
            platform: PlatformInfo = PlatformInfo(),
            images: Images = None,
            runningContainers: RunningContainers = None,
            cpu: CPU = CPU(),
            memory: Memory = Memory()):
        Resources.__init__(
            self,
            cpu=cpu,
            memory=memory)
        self.platform = platform
        if images is None:
            self.images = set()
        else:
            self.images = images
        if runningContainers is None:
            self.runningContainers = set()
        else:
            self.runningContainers = runningContainers

    def toDict(self):
        inDict = {
            'platform': self.platform.toDict(),
            'images': list(self.images),
            'runningContainers': list(self.runningContainers),
            'cpu': self.cpu.toDict(),
            'memory': self.memory.toDict()}
        return inDict

    @staticmethod
    def fromDict(inDict: Dict):
        if isinstance(inDict['images'], list):
            inDict['images'] = set(inDict['images'])
        if isinstance(inDict['runningContainers'], list):
            inDict['runningContainers'] = set(inDict['runningContainers'])
        profiles = ActorResources(
            platform=PlatformInfo.fromDict(inDict['platform']),
            images=inDict['images'],
            runningContainers=inDict['runningContainers'],
            cpu=CPU.fromDict(inDict['cpu']),
            memory=Memory.fromDict(inDict['memory']))
        return profiles
