from logging import Logger

from ..logger import LoggerManager
from ...component import BasicComponent
from ...connection import HandlerReturn
from ...connection import MessageReceived
from ...types import ComponentRole
from ...types import MessageSubType
from ...types import MessageType
from ...types import ProcessingTime
from ...types import ActorResources
from ...types import SynchronizedAttribute


class LogHandler:

    def __init__(
            self,
            basicComponent: BasicComponent,
            debugLogger: Logger,
            loggerManager: LoggerManager):
        self.basicComponent = basicComponent
        self.debugLogger = debugLogger
        self.loggerManager = loggerManager

    def handleHostResources(self, message: MessageReceived) -> HandlerReturn:
        data = message.data
        hostResources = ActorResources.fromDict(data['actorResources'])
        hostNameConsistent = message.source.nameConsistent
        toMerge = {hostNameConsistent: hostResources}
        self.loggerManager.mergeResources(toMerge)
        return None

    def handleImagesAndRunningContainers(
            self, message: MessageReceived) -> HandlerReturn:
        hostNameConsistent = message.source.nameConsistent
        images = message.data['images']
        imagesToMerge = {hostNameConsistent: set(images)}
        self.loggerManager.mergeImages(imagesToMerge)

        runningContainers = message.data['runningContainers']
        runningContainersToMerge = {hostNameConsistent: set(runningContainers)}
        self.loggerManager.mergeRunningContainers(runningContainersToMerge)
        return None

    def handleDataRate(self, message: MessageReceived) -> HandlerReturn:
        dataRate = message.data['dataRate']
        self.loggerManager.mergeDataRate(dataRate)
        return None

    def handleDelays(self, message: MessageReceived) -> HandlerReturn:
        delays = message.data['delays']
        sourceName = message.source.nameConsistent
        toMerge = {sourceName: delays}
        self.loggerManager.mergeDelay(toMerge)
        return None

    def handleLatency(self, message: MessageReceived) -> HandlerReturn:
        latency = message.data['latency']
        self.loggerManager.mergeLatency(latency)
        return None

    def handleMedianReceivedPacketSize(
            self, message: MessageReceived) -> HandlerReturn:
        sizes = message.data['sizes']
        destName = message.source.nameConsistent
        toMerge = {destName: sizes}
        self.loggerManager.mergePacketSize(toMerge)
        return None

    def handleMedianProcessingTime(
            self, message: MessageReceived) -> HandlerReturn:
        data = message.data
        processingTimeInJson = data['medianProcessTime']
        processingTime = ProcessingTime.fromDict(processingTimeInJson)
        sourceName = message.source.nameConsistent
        toMerge = {
            sourceName: processingTime,
            processingTime.taskExecutorName: processingTime}
        self.loggerManager.mergeProcessingTime(toMerge)
        return None

    def handleResponseTime(self, message: MessageReceived) -> HandlerReturn:
        responseTime = message.data['responseTime']
        sourceName = message.source.nameConsistent
        toMerge = {sourceName: responseTime}
        self.loggerManager.mergeResponseTime(toMerge)
        return None

    def handleRequestProfiles(self, message: MessageReceived):
        self._handleRequestProfiles(
            self, message=message, attributeName='loggerManager')

    @SynchronizedAttribute
    def _handleRequestProfiles(
            self, message: MessageReceived, attributeName='loggerManager'):
        if not message.source.role == ComponentRole.MASTER:
            return
        data = {'profiles': self.loggerManager.toDict()}
        self.basicComponent.sendMessage(
            messageType=MessageType.LOG,
            messageSubType=MessageSubType.ALL_RESOURCES_PROFILES,
            data=data,
            destination=message.source)

    def handleProfiles(self, message: MessageReceived):
        self._handleProfiles(
            self, message=message, attributeName='loggerManager')

    @SynchronizedAttribute
    def _handleProfiles(
            self, message: MessageReceived, attributeName='loggerManager'):
        data = message.data
        self.loggerManager.mergeFromDict(inDict=data['profiles'])
        return
