from json.decoder import JSONDecodeError
from threading import Lock
from time import sleep

from iperf3 import Client as NetProfClient
from iperf3 import Server as NetProfServer
from pythonping import ping as testLatency

from ..profiler.base import MasterProfiler
from ...component import BasicComponent
from ...connection import MessageReceived
from ...types import Component
from ...types import MessageSubSubType
from ...types import MessageSubType
from ...types import MessageType


class ProfilingHandler:
    def __init__(
            self,
            basicComponent: BasicComponent,
            profiler: MasterProfiler):

        self.profiler = profiler
        self.basicComponent = basicComponent
        self.debugLogger = self.basicComponent.debugLogger
        self._runningIperfClient = Lock()
        self._runningIperfServer = Lock()

    def handleDataRateReceive(self, message: MessageReceived):
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
        self.debugLogger.info(
            'Running net profiling from %s to %s as target',
            sourceAddr[0],
            self.basicComponent.addr[0])
        self.runDataRateReceive(sourceHostID)

    def handleDataRateSend(self, message: MessageReceived):
        self.runDataRateSend(message)

    def handleDataRateResult(self, message: MessageReceived):
        data = message.data
        sourceHostID = data['sourceHostID']
        targetHostID = data['targetHostID']
        dataRateResult = data['dataRateResult']
        systemPerformance = self.profiler.loggerManager.systemPerformance
        if sourceHostID not in systemPerformance.dataRate:
            self.profiler.loggerManager.systemPerformance.dataRate[
                sourceHostID] = {}
        self.profiler.loggerManager.systemPerformance.dataRate[sourceHostID][
            targetHostID] = dataRateResult
        self.profiler.dataRateTestEvents[sourceHostID][targetHostID].set()
        self.debugLogger.info(
            'Received BPS result from %s to %s',
            sourceHostID,
            targetHostID)

    def handleLatencyResult(self, message: MessageReceived):
        data = message.data
        sourceHostID = data['sourceHostID']
        targetHostID = data['targetHostID']
        latencyResult = data['latencyResult']

        if sourceHostID not in self.profiler.loggerManager.systemPerformance.latency:
            self.profiler.loggerManager.systemPerformance.latency[
                sourceHostID] = {}
        self.profiler.loggerManager.systemPerformance.latency[sourceHostID][
            targetHostID] = latencyResult
        self.profiler.latencyTestEvents[sourceHostID][targetHostID].set()
        self.debugLogger.info(
            'Received Ping result from %s to %s',
            sourceHostID,
            targetHostID)

    def runDataRateReceive(
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
                self.debugLogger.info(
                    'Uploaded net profiling log from %s to %s ',
                    sourceHostID,
                    self.basicComponent.hostID)
                break
            except (AttributeError, IndexError, JSONDecodeError):
                self.debugLogger.warning('Retry receiving')
                sleep(1)
                continue
        self._runningIperfServer.release()

    def runDataRateSend(self, message: MessageReceived):
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
                self.debugLogger.warning(
                    'Retry connecting %s',
                    source.addr[0])
                sleep(1)
                continue
        sleep(3)
        self.debugLogger.info(
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
        self.debugLogger.info(
            'Uploaded ping from %s to %s',
            self.basicComponent.addr[0],
            source.addr[0])
        self._runningIperfClient.release()
