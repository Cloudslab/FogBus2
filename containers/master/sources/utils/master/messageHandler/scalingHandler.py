from ..profiler.base import MasterProfiler
from ...component import BasicComponent
from ...connection import MessageReceived
from ...types import MessageSubType
from ...types import MessageType


class ScalingHandler:
    def __init__(
            self,
            basicComponent: BasicComponent,
            profiler: MasterProfiler):
        self.profiler = profiler
        self.basicComponent = basicComponent

    def handleGetProfiler(self, message: MessageReceived):
        source = message.source
        data = {'allProfiles': self.profiler.loggerManager.toDict()}
        self.basicComponent.sendMessage(
            messageType=MessageType.SCALING,
            messageSubType=MessageSubType.PROFILES_INFO,
            data=data,
            destination=source)

    def handleProfilerInfo(self, message: MessageReceived):
        data = message.data
        profiles = data['allProfiles']
        self.profiler.loggerManager.fromDict(profiles)
