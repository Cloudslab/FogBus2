from json.decoder import JSONDecodeError
from threading import Lock
from time import sleep

from iperf3 import Client as NetProfClient
from iperf3 import Server as NetProfServer
from pythonping import ping as testLatency

from ..initiator.complete import Initiator
from ..profiler.actor import ActorProfiler
from ...component import BasicComponent
from ...connection.message.received import MessageReceived
from ...container.manager import ContainerManager
from ...resourceDiscovery.resourceDiscovery import ResourcesDiscovery
from ...types import Component
from ...types.message.subSubType import MessageSubSubType
from ...types.message.subType import MessageSubType
from ...types.message.type import MessageType


class ActorMessageHandler:

    def __init__(
            self,
            resourcesDiscovery: ResourcesDiscovery,
            containerManager: ContainerManager,
            basicComponent: BasicComponent,
            initiator: Initiator,
            profiler: ActorProfiler):
        self.resourcesDiscovery = resourcesDiscovery
        self.containerManager = containerManager
        self.profiler = profiler
        self.initiator = initiator
        self.basicComponent = basicComponent
        self.basicComponent.handleMessage = self.handleMessage
        self._runningIperfClient = Lock()
        self._runningIperfServer = Lock()

    def handleMessage(self, message: MessageReceived):
        if message.typeIs(
                messageType=MessageType.PLACEMENT,
                messageSubType=MessageSubType.RUN_TASK_EXECUTOR):
            self.handleInitTaskExecutor(message)
            return
        if message.typeIs(
                messageType=MessageType.RESOURCE_DISCOVERY,
                messageSubType=MessageSubType.ADVERTISE_MASTER):
            self.handleAdvertise(message)
            return
        if message.typeIs(
                messageType=MessageType.SCALING,
                messageSubType=MessageSubType.INIT_NEW_MASTER):
            self.handleInitMaster(message)
            return
        if message.typeIs(
                messageType=MessageType.PROFILING,
                messageSubType=MessageSubType.DATA_RATE_TEST,
                messageSubSubType=MessageSubSubType.RECEIVE):
            self.handleDataRateTestReceive(message)
            return
        if message.typeIs(
                messageType=MessageType.PROFILING,
                messageSubType=MessageSubType.DATA_RATE_TEST,
                messageSubSubType=MessageSubSubType.SEND):
            self.handleDataRateTestSend(message)
            return

        if message.typeIs(
                messageType=MessageType.REGISTRATION,
                messageSubType=MessageSubType.REGISTERED):
            self.handleRegistered(message)
            return

        if message.typeIs(
                messageType=MessageType.MessageType.RESOURCE_DISCOVERY,
                messageSubType=MessageSubType.PROBE,
                messageSubSubType=MessageSubSubType.RESULT):
            self.resourcesDiscovery.handleMessage(message=message)
            return

    def handleRegistered(self, message: MessageReceived):
        source = message.source
        self.basicComponent.master = source
        data = message.data
        componentID = data['actorID']
        name = data['name']
        nameLogPrinting = data['nameLogPrinting']
        nameConsistent = data['nameConsistent']
        self.basicComponent.setName(
            addr=self.basicComponent.addr,
            name=name,
            nameLogPrinting=nameLogPrinting,
            nameConsistent=nameConsistent,
            componentID=componentID,
            setIsRegistered=True)
        self.containerManager.tryRenamingContainerName(
            newName=self.basicComponent.nameLogPrinting)
        self.basicComponent.debugLogger.info("Registered, running...")

    def handleInitTaskExecutor(self, message: MessageReceived):
        data = message.data
        if self.profiler.resources.cpu.utilization > .8:
            return
        if self.profiler.resources.memory.utilization > .8:
            return

        userID = data['userID']
        userName = data['userName']
        taskName = data['taskName']
        taskToken = data['taskToken']
        childTaskTokens = data['childrenTaskTokens']
        self.initiator.initTaskExecutor(
            userID=userID,
            userName=userName,
            taskName=taskName,
            taskToken=taskToken,
            childTaskTokens=childTaskTokens,
            isContainerMode=self.containerManager.isContainerMode)

    def canInitComponent(
            self,
            cpuUtilizationThreshold: float = .8,
            memoryUtilizationThreshold: float = .8) -> bool:
        cpuUtilization = self.profiler.resources.cpu.utilization
        if cpuUtilization > cpuUtilizationThreshold:
            self.basicComponent.debugLogger.debug(
                'CPU utilization is high: %f', cpuUtilization)
            return False
        memoryUtilization = self.profiler.resources.memory.utilization
        if memoryUtilization > memoryUtilizationThreshold:
            self.basicComponent.debugLogger.debug(
                'Memory utilization is high: %f', memoryUtilization)
            return False
        return True

    def handleInitMaster(self, message: MessageReceived):
        self.basicComponent.debugLogger.debug('Received init master msg')
        if not self.canInitComponent():
            self.basicComponent.debugLogger.info(
                'Cannot create another actor for %s' % str(message.source.addr))
            return
        source = message.source
        self.initiator.initMaster(
            me=self.basicComponent.me,
            remoteLogger=self.basicComponent.remoteLogger,
            createdBy=source,
            message=message,
            isContainerMode=self.containerManager.isContainerMode)
        return

    def handleAdvertise(self, message: MessageReceived):
        if not self.canInitComponent():
            self.basicComponent.debugLogger.info(
                'Ignore advertisement from %s' % str(message.source.addr))
            return
        source = message.source
        self.initiator.initActor(
            me=self.basicComponent.me,
            remoteLogger=self.basicComponent.remoteLogger,
            master=source,
            isContainerMode=self.containerManager.isContainerMode)
        return

    def handleDataRateTestReceive(self, message: MessageReceived):
        data = message.data
        sourceAddr = data['sourceAddr']
        sourceHostID = data['sourceHostID']
        messageDest = Component(addr=sourceAddr, hostID=sourceHostID)
        data = {'targetHostID': self.basicComponent.hostID}
        self.basicComponent.sendMessage(
            messageType=MessageType.PROFILING,
            messageSubType=MessageSubType.DATA_RATE_TEST,
            messageSubSubType=MessageSubSubType.SEND,
            data=data,
            destination=messageDest)
        self.basicComponent.debugLogger.info(
            'Running net profiling from %s to %s as target',
            sourceAddr[0],
            self.basicComponent.addr[0])
        self.runDataRateTestServer(sourceHostID)

    def runDataRateTestServer(
            self,
            sourceHostID: str):
        self._runningIperfServer.acquire()
        server = NetProfServer()
        server.bind_address = self.basicComponent.addr[0]
        server.port = 60000
        while True:
            try:
                self.basicComponent.debugLogger.debug('Run iperf server')
                dataRateResult = server.run()
                if 'error' in dataRateResult.json:
                    sleep(1)
                    continue
                data = {
                    'sourceHostID': sourceHostID,
                    'targetHostID': self.basicComponent.hostID,
                    'dataRateResult': dataRateResult.received_bps}
                self.basicComponent.sendMessage(
                    messageType=MessageType.PROFILING,
                    messageSubType=MessageSubType.DATA_RATE_TEST,
                    messageSubSubType=MessageSubSubType.RESULT,
                    data=data,
                    destination=self.basicComponent.master)
                self.basicComponent.debugLogger.info(
                    'Uploaded net profiling log from %s to %s ',
                    sourceHostID,
                    self.basicComponent.hostID)
                break
            except (AttributeError, IndexError, JSONDecodeError):
                self.basicComponent.debugLogger.warning('Retry receiving')
                sleep(1)
                continue
        self._runningIperfServer.release()

    def handleDataRateTestSend(self, message: MessageReceived):
        self._runningIperfClient.acquire()
        data = message.data
        source = message.source
        client = NetProfClient()
        client.bind_address = self.basicComponent.addr[0]
        client.server_hostname = source.addr[0]
        client.port = 60000
        client.duration = 2
        maxRound = 1000
        while maxRound > 0:
            maxRound -= 1
            try:
                self.basicComponent.debugLogger.debug('Run iperf client')
                sleep(3)
                res = client.run()
                if 'error' in res.json:
                    sleep(1)
                    continue
                break
            except (AttributeError, IndexError, JSONDecodeError, OSError):
                self.basicComponent.debugLogger.warning(
                    'Retry connecting %s',
                    source.addr[0])
                sleep(1)
                continue
        sleep(3)
        self.basicComponent.debugLogger.info(
            'Done net profiling from %s to %s as source',
            self.basicComponent.addr[0],
            source.addr[0])
        latencyResponseList = testLatency(
            source.addr[0],
            size=40,
            count=10)
        latencyResult = latencyResponseList.rtt_avg_ms

        data = {
            'sourceHostID': self.basicComponent.hostID,
            'targetHostID': data['targetHostID'],
            'latencyResult': latencyResult}
        self.basicComponent.sendMessage(
            messageType=MessageType.PROFILING,
            messageSubType=MessageSubType.LATENCY_TEST,
            messageSubSubType=MessageSubSubType.RESULT,
            data=data,
            destination=self.basicComponent.master)
        self.basicComponent.debugLogger.info(
            'Uploaded ping from %s to %s',
            self.basicComponent.addr[0],
            source.addr[0])
        self._runningIperfClient.release()
