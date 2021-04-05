from .logHandler import LogHandler
from ..logger import LoggerManager
from ...component import BasicComponent
from ...connection import HandlerReturn
from ...connection import MessageReceived
from ...resourceDiscovery.resourceDiscovery import ResourcesDiscovery
from ...types import MessageSubType
from ...types import MessageType


class RemoteLoggerMessageHandler:

    def __init__(self,
                 resourcesDiscovery: ResourcesDiscovery,
                 basicComponent: BasicComponent,
                 loggerManager: LoggerManager):
        self.resourcesDiscovery = resourcesDiscovery
        self.basicComponent = basicComponent
        self.basicComponent.handleMessage = self.handleMessage
        self.logHandler: LogHandler = LogHandler(
            basicComponent=self.basicComponent,
            debugLogger=self.basicComponent.debugLogger,
            loggerManager=loggerManager)

    def handleMessage(self, message: MessageReceived):
        messageToRespond = None
        if message.typeIs(messageType=MessageType.LOG):
            messageToRespond = self.handleLog(message)
        elif message.typeIs(messageType=MessageType.RESOURCE_DISCOVERY):
            self.resourcesDiscovery.handleMessage(message=message)
        if messageToRespond is None:
            return
        self.basicComponent.sendMessage(messageToSend=messageToRespond)

    def handleLog(self, message: MessageReceived) -> HandlerReturn:
        if message.typeIs(
                messageSubType=MessageSubType.PROFILES):
            self.logHandler.handleProfiles(message)
            return
        if message.typeIs(
                messageSubType=MessageSubType.REQUEST_PROFILES):
            self.logHandler.handleRequestProfiles(message)
            return
        if message.typeIs(
                messageSubType=MessageSubType.MEDIAN_RECEIVED_PACKET_SIZE):
            self.logHandler.handleMedianReceivedPacketSize(message)
            return
        if message.typeIs(
                messageSubType=MessageSubType.MEDIAN_PROCESSING_TIME):
            self.logHandler.handleMedianProcessingTime(message)
            return
        if message.typeIs(
                messageSubType=MessageSubType.HOST_RESOURCES):
            self.logHandler.handleHostResources(message)
            return
        if message.typeIs(
                messageSubType=MessageSubType.RESPONSE_TIME):
            self.logHandler.handleResponseTime(message)
            return
        if message.typeIs(
                messageSubType=MessageSubType.DELAYS):
            self.logHandler.handleDelays(message)
            return
        if message.typeIs(
                messageSubType=MessageSubType.DATA_RATE_TEST):
            self.logHandler.handleDataRate(message)
            return
        if message.typeIs(
                messageSubType=MessageSubType.LATENCY):
            self.logHandler.handleLatency(message)
            return
        if message.typeIs(
                messageSubType=MessageSubType.CONTAINER_IMAGES_AND_RUNNING_CONTAINERS):
            self.logHandler.handleImagesAndRunningContainers(message)
            return
