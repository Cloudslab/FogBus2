import os
from json import dump
from pprint import pformat
from threading import Thread
from time import sleep
from time import time

from ..applications.base import ApplicationUserSide
from ..registration.manager import RegistrationManager
from ...component import BasicComponent
from ...connection.message.received import MessageReceived
from ...container.manager import ContainerManager
from ...resourceDiscovery.resourceDiscovery import ResourcesDiscovery
from ...tools.terminate import terminate
from ...types import ComponentRole
from ...types import MessageSubType
from ...types import MessageType


class UserMessageHandler:
    def __init__(
            self,
            resourcesDiscovery: ResourcesDiscovery,
            containerManager: ContainerManager,
            basicComponent: BasicComponent,
            actuator: ApplicationUserSide,
            registrationManager: RegistrationManager):

        self.resourcesDiscovery = resourcesDiscovery
        self.registrationManager = registrationManager
        self.actuator = actuator
        self.containerManager = containerManager
        self.basicComponent = basicComponent
        self.basicComponent.handleMessage = self.handleMessage
        self.lastDataSentTime = 0
        self.registerTime = 0

    def handleMessage(self, message: MessageReceived):
        if message.typeIs(
                messageType=MessageType.REGISTRATION,
                messageSubType=MessageSubType.REGISTERED):
            self.handleRegistered(message=message)
        elif message.typeIs(
                messageType=MessageType.ACKNOWLEDGEMENT,
                messageSubType=MessageSubType.SERVICE_READY):
            self.handleReady()
        elif message.typeIs(
                messageType=MessageType.DATA,
                messageSubType=MessageSubType.FINAL_RESULT):
            self.handleResult(message=message)
        elif message.typeIs(
                messageType=MessageType.EXPERIMENTAL,
                messageSubType=MessageSubType.ACTORS_COUNT):
            self.handleActorsCount(message=message)
        elif message.typeIs(
                messageType=MessageType.SCALING,
                messageSubType=MessageSubType.CONNECT_TO_NEW_MASTER):
            self.handleForward(message=message)
        elif message.typeIs(
                messageType=MessageType.ACKNOWLEDGEMENT,
                messageSubType=MessageSubType.NO_ACTOR):
            self.handleNoActor(message=message)
        elif message.typeIs(
                messageType=MessageType.TERMINATION,
                messageSubType=MessageSubType.STOP):
            self.handleStop(message=message)

    def handleStop(self, message: MessageReceived):
        data = message.data
        durationTime = time() * 1000 - self.actuator.startTime
        hours, remainder = divmod(durationTime / 1000, 3600)
        minutes, seconds = divmod(remainder, 60)
        packetSize = data['packetSize']
        info = {
            'ApplicationName': self.actuator.appName,
            'ResponseTime': '%.2f ms' % self.actuator.responseTime.median(),
            'RanTime': '%d hours, %d mins, %.1f secs' % (
                hours, minutes, seconds),
            'PacketSize': int(packetSize)}
        self.basicComponent.debugLogger.info(
            '\n========== Application Summary ==========\n'
            '%s'
            '\n=========================================',
            pformat(info, indent=4))
        self.basicComponent.debugLogger.debug('Bye')
        terminate()

    def handleRegistered(self, message: MessageReceived):
        source = message.source
        self.basicComponent.master = source
        data = message.data
        componentID = data['userID']
        name = data['name']
        nameLogPrinting = data['nameLogPrinting']
        nameConsistent = data['nameConsistent']
        self.basicComponent.setName(
            addr=self.basicComponent.addr,
            name=name,
            componentID=componentID,
            nameLogPrinting=nameLogPrinting,
            nameConsistent=nameConsistent,
            setIsRegistered=True)
        self.basicComponent.debugLogger.info(
            "Registered at %s. Waiting for resources to be ready ..." %
            str(source.addr))

    def saveRequestTime(self):
        currTime = time() * 1000
        timeCost = currTime - self.registrationManager.requestSentTime
        filename = '%s@%s@%f.json' % (
            self.registrationManager.appName,
            self.basicComponent.nameLogPrinting,
            currTime)
        f = open(filename, 'w+')
        f.write(str(timeCost))
        f.close()
        terminate()

    def handleReady(self):
        # self.basicComponent.debugLogger.info(
        #     'RRT: %f', time() * 1000 - self.registerTime)
        # import os
        # sleep(5)
        # self.basicComponent.sendMessage(
        #     messageType=MessageType.TERMINATION,
        #     messageSubType=MessageSubType.EXIT,
        #     data={'reason': 'Manually interrupted.'},
        #     destination=self.basicComponent.master)
        # sleep(5)
        # os._exit(0)
        Thread(target=self.ready, name='Actuator').start()

    def handleResult(self, message: MessageReceived):

        result = message.data['finalResult']
        self.actuator.resultForActuator.put(result)
        # self.saveResponseTime()

    def handleActorsCount(self, message: MessageReceived):
        data = message.data
        self.registrationManager.actorsCount = data['actorsCount']

    def handleForward(self, message: MessageReceived):
        data = message.data
        addr = data['masterAddr']
        masterAddr = (addr[0], addr[1])
        # give the new Master some time to rise
        self.basicComponent.debugLogger.info(
            'Request is forwarding to %s' % str(masterAddr))
        self.basicComponent.debugLogger.info(
            'Lookup %s at %s', ComponentRole.MASTER.value, str(masterAddr))
        while not self.registrationManager.testConnectivity(addr=masterAddr):
            sleep(1)
        self.basicComponent.debugLogger.info(
            'Found %s at %s', ComponentRole.MASTER.value, str(masterAddr))
        self.registrationManager.registerAt(masterAddr)

    def handleNoActor(self, message: MessageReceived):
        self.basicComponent.debugLogger.warning(
            'There is no %s at %s, would you like to discover available %s? '
            'Otherwise exit. (y/N): ',
            ComponentRole.ACTOR.value,
            message.source.nameLogPrinting,
            ComponentRole.MASTER.value)
        userInput = input()
        if userInput not in {'y', 'Y', 'yes', 'Yes'}:
            self.basicComponent.debugLogger.info('Bye!')
            terminate()
        self.resourcesDiscovery.discoverAndCommunicate(
            targetRole=ComponentRole.MASTER)
        self.registrationManager.registerAt(self.basicComponent.master.addr)

    def ready(self):
        self.basicComponent.debugLogger.info('Resources is ready.')
        self.actuator.start()

        while True:
            data = {
                'userID': self.basicComponent.componentID,
                'sensoryData': self.actuator.dataToSubmit.get()}
            self.basicComponent.sendMessage(
                messageType=MessageType.DATA,
                messageSubType=MessageSubType.SENSORY_DATA,
                data=data,
                destination=self.basicComponent.master)
            self.lastDataSentTime = time() * 1000

    def saveResponseTime(self):
        if self.actuator.responseTimeCount < 7:
            return
        logFilename = 'log/responseTime.json'
        if os.path.exists(logFilename):
            return
        self.basicComponent.debugLogger.info(self.actuator.responseTimeCount)
        if not os.path.exists('log'):
            os.mkdir('log')
        with open(logFilename, 'w+') as f:
            nameLogPrinting = self.basicComponent.nameLogPrinting
            content = {
                nameLogPrinting: self.actuator.responseTime.median()}
            dump(content, f)
            f.close()
            self.basicComponent.debugLogger.info(content)
