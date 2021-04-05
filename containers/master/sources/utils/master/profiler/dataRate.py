from collections import defaultdict
from threading import Event
from time import sleep
from typing import DefaultDict

from ..logger import LoggerManager
from ..registry.registered.actors import RegisteredActors
from ...component import BasicComponent
from ...connection import MessageToSend
from ...types import MessageSubSubType
from ...types import MessageSubType
from ...types import MessageType


class DataRateProfiler:

    def __init__(
            self,
            basicComponent: BasicComponent,
            loggerManager: LoggerManager,
            minActors: int):
        self.basicComponent = basicComponent
        self.loggerManager = loggerManager
        self.minHosts = minActors
        self.latencyTestEvents: DefaultDict[
            str, DefaultDict[str, Event]] = defaultdict(
            lambda: defaultdict(lambda: Event()))
        self.dataRateTestEvents: DefaultDict[
            str, DefaultDict[str, Event]] = defaultdict(
            lambda: defaultdict(lambda: Event()))
        self.dataRateTestEvent: Event = Event()
        self.gotEnoughActors: Event = Event()
        self.registeredActors = None

    def periodicallyProfileDataRate(self):
        self.gotEnoughActors.wait()
        self.basicComponent.debugLogger.debug('Profiling data rate ...')
        if self.registeredActors is None:
            return
        self.profileDataRate(registeredActors=self.registeredActors)

    def profileDataRate(self, registeredActors: RegisteredActors):
        minHosts = self.minHosts
        self.basicComponent.debugLogger.info('Waiting for %d hosts',
                                             self.minHosts)
        while len(registeredActors) < minHosts:
            sleep(1)
        components = registeredActors.copyAll()
        components.append(self.basicComponent.master)
        self.basicComponent.debugLogger.info(
            '%d hosts connected, begin network profiling', self.minHosts)
        count = 1
        total = len(components) * len(components)
        for source in components:
            for target in components:
                sleep(1)
                self.basicComponent.debugLogger.debug('%d/%d', count, total)
                count += 1
                sourceHostID = source.hostID
                targetHostID = target.hostID
                if targetHostID == sourceHostID:
                    continue
                if sourceHostID in \
                        self.loggerManager.systemPerformance.dataRate:
                    if targetHostID in \
                            self.loggerManager.systemPerformance.dataRate[
                                sourceHostID]:
                        continue
                self.runDataRateTest(
                    registeredActors, sourceHostID, targetHostID)
                self.latencyTestEvents[sourceHostID][targetHostID].wait()
                self.dataRateTestEvents[sourceHostID][targetHostID].wait()
        self.dataRateTestEvent.set()
        self.basicComponent.debugLogger.info(
            'Finished profiling data rate and latency.')

    def getHosts(self, registeredActors: RegisteredActors):
        hosts = {self.basicComponent.hostID}
        for actor in registeredActors.copyAll():
            if actor.hostID in hosts:
                continue
            hosts.add(actor.hostID)
        return hosts

    def runDataRateTest(
            self, registeredActors: RegisteredActors, sourceHostID: str,
            targetHostID: str):
        if sourceHostID == targetHostID:
            return
        if sourceHostID == self.basicComponent.hostID:
            sourceComponent = self.basicComponent.me
        else:
            sourceComponent = registeredActors[sourceHostID]

        if targetHostID == self.basicComponent.hostID:
            targetComponent = self.basicComponent.me
        else:
            targetComponent = registeredActors[targetHostID]

        data = {
            'sourceAddr': sourceComponent.addr,
            'sourceHostID': sourceComponent.hostID}
        message = MessageToSend(
            messageType=MessageType.PROFILING,
            messageSubType=MessageSubType.DATA_RATE_TEST,
            messageSubSubType=MessageSubSubType.RECEIVE,
            data=data,
            destination=targetComponent
        )
        self.basicComponent.sendMessage(messageToSend=message)
        self.basicComponent.debugLogger.info(
            'Waiting for net profile from %s to %s',
            sourceComponent.addr[0],
            targetComponent.addr[0])
