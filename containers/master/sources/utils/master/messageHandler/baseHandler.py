from .acknowledgementHandler import AcknowledgementHandler
from .dataHandler import DataHandler
from .experimentalHandler import ExperimentalHandler
from .logHandler import LogHandler
from .placementHandler import PlacementHandler
from .profilingHandler import ProfilingHandler
from .registrationHandler import RegistrationHandler
from .resourcesDiscoveryHandler import ResourcesDiscoveryHandler
from .scalingHandler import ScalingHandler
from .terminationHandler import TerminationHandler
from ..logger import LoggerManager
from ..profiler.base import MasterProfiler
from ..registry.base import Registry
from ..resourcesDiscovery import MasterResourcesDiscovery
from ...component import BasicComponent
from ...connection import HandlerReturn
from ...connection import MessageReceived
from ...types import MessageSubSubType
from ...types import MessageSubType
from ...types import MessageType


class MasterMessageHandler:

    def __init__(
            self,
            basicComponent: BasicComponent,
            registry: Registry,
            loggerManager: LoggerManager,
            profiler: MasterProfiler,
            resourcesDiscovery: MasterResourcesDiscovery):
        self.registry = registry
        self.basicComponent = basicComponent
        self.basicComponent.handleMessage = self.handleMessage
        self.profiler = profiler
        self.loggerManager = loggerManager
        self.resourcesDiscovery = resourcesDiscovery
        self.acknowledgementHandler = AcknowledgementHandler(
            registry=registry,
            basicComponent=basicComponent)
        self.terminationHandler = TerminationHandler(
            basicComponent=self.basicComponent,
            registry=self.registry,
            acknowledgementHandler=self.acknowledgementHandler)
        self.logHandler = LogHandler(loggerManager=self.loggerManager)
        self.dataHandler = DataHandler(
            basicComponent=self.basicComponent,
            registry=self.registry)
        self.experimentalHandler = ExperimentalHandler(
            registry=self.registry)
        self.placementHandler = PlacementHandler(
            registry=self.registry)
        self.profilingHandler = ProfilingHandler(
            basicComponent=self.basicComponent,
            profiler=self.profiler)
        self.registrationHandler = RegistrationHandler(
            basicComponent=self.basicComponent,
            registry=self.registry,
            profiler=self.profiler)
        self.resourcesDiscoveryHandler = ResourcesDiscoveryHandler(
            basicComponent=self.basicComponent,
            resourcesDiscovery=self.resourcesDiscovery)
        self.scalingHandler: ScalingHandler = ScalingHandler(
            basicComponent=self.basicComponent,
            profiler=self.profiler)

    def handleMessage(self, message: MessageReceived):
        messageToRespond = None
        if message.typeIs(MessageType.ACKNOWLEDGEMENT):
            messageToRespond = self.handleAcknowledgement(message)
        elif message.typeIs(MessageType.DATA):
            messageToRespond = self.handleData(message)
        elif message.typeIs(MessageType.EXPERIMENTAL):
            messageToRespond = self.handleExperimental(message)
        elif message.typeIs(MessageType.LOG):
            messageToRespond = self.handleLog(message)
        elif message.typeIs(MessageType.PLACEMENT):
            messageToRespond = self.handlePlacement(message)
        elif message.typeIs(MessageType.PROFILING):
            messageToRespond = self.handleProfiling(message)
        elif message.typeIs(MessageType.REGISTRATION):
            messageToRespond = self.handleRegistration(message)
        elif message.typeIs(MessageType.RESOURCE_DISCOVERY):
            messageToRespond = self.handleResourcesDiscovery(message)
        elif message.typeIs(MessageType.SCALING):
            messageToRespond = self.handleScaling(message)
        elif message.typeIs(MessageType.TERMINATION):
            messageToRespond = self.handleTermination(message)
        if messageToRespond is None:
            return
        self.basicComponent.sendMessage(messageToSend=messageToRespond)

    def handleLog(self, message: MessageReceived) -> HandlerReturn:
        if message.typeIs(messageSubType=MessageSubType.ALL_RESOURCES_PROFILES):
            return self.logHandler.handleProfiles(message)
        return

    def handleAcknowledgement(self, message: MessageReceived) -> HandlerReturn:
        if message.typeIs(messageSubType=MessageSubType.READY):
            return self.acknowledgementHandler.handleReady(message)
        elif message.typeIs(messageSubType=MessageSubType.WAITING):
            return self.acknowledgementHandler.handleTaskExecutorWaiting(
                message)
        return

    def handleData(self, message: MessageReceived) -> HandlerReturn:
        if message.typeIs(messageSubType=MessageSubType.SENSORY_DATA):
            return self.dataHandler.handleSensoryData(message)
        elif message.typeIs(messageSubType=MessageSubType.FINAL_RESULT):
            return self.dataHandler.handleResult(message)
        return

    def handleExperimental(self, message: MessageReceived) -> HandlerReturn:
        if message.typeIs(messageSubType=MessageSubType.ACTORS_COUNT):
            return self.experimentalHandler.handleActorsCount(message)
        return

    def handlePlacement(self, message: MessageReceived) -> HandlerReturn:
        if message.typeIs(messageSubType=MessageSubType.LOOKUP):
            return self.placementHandler.handleLookup(message)
        return

    def handleProfiling(self, message: MessageReceived) -> HandlerReturn:
        if message.typeIs(
                messageSubType=MessageSubType.DATA_RATE_TEST,
                messageSubSubType=MessageSubSubType.RECEIVE):
            return self.profilingHandler.handleDataRateReceive(message)
        elif message.typeIs(
                messageSubType=MessageSubType.DATA_RATE_TEST,
                messageSubSubType=MessageSubSubType.SEND):

            return self.profilingHandler.handleDataRateSend(message)
        elif message.typeIs(
                messageSubType=MessageSubType.DATA_RATE_TEST,
                messageSubSubType=MessageSubSubType.RESULT):
            return self.profilingHandler.handleDataRateResult(message)
        elif message.typeIs(
                messageSubType=MessageSubType.LATENCY_TEST,
                messageSubSubType=MessageSubSubType.RESULT):
            return self.profilingHandler.handleLatencyResult(message)
        return

    def handleRegistration(self, message: MessageReceived) -> HandlerReturn:
        if message.typeIs(messageSubType=MessageSubType.REGISTER):
            return self.registrationHandler.handleRegister(message)
        return

    def handleResourcesDiscovery(
            self, message: MessageReceived) -> HandlerReturn:
        if message.typeIs(messageSubType=MessageSubType.REQUEST_ACTORS_INFO):
            return self.resourcesDiscoveryHandler.handleActorsAddr(message)
        elif message.typeIs(messageSubType=MessageSubType.ACTORS_INFO):
            return self.resourcesDiscoveryHandler.handleActorsAddrResult(
                message)
        return self.resourcesDiscovery.handleMessage(message)

    def handleScaling(self, message: MessageReceived) -> HandlerReturn:
        if message.typeIs(messageSubType=MessageSubType.GET_PROFILES, ):
            return self.scalingHandler.handleGetProfiler(message)
        elif message.typeIs(messageSubType=MessageSubType.PROFILES_INFO):
            return self.scalingHandler.handleProfilerInfo(message)
        return

    def handleTermination(self, message: MessageReceived) -> HandlerReturn:
        if message.typeIs(messageSubType=MessageSubType.EXIT):
            return self.terminationHandler.handleExit(message)
        return
