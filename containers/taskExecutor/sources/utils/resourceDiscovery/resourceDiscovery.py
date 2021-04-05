from ipaddress import ip_network
from pprint import pformat
from threading import Event
from time import sleep

from .discovered import DiscoveredManager
from ..component import BasicComponent
from ..config import ConfigActor
from ..config import ConfigMaster
from ..config import ConfigRemoteLogger
from ..config import ConfigTaskExecutor
from ..config import ConfigUser
from ..connection.message.received import MessageReceived
from ..tools import terminate
from ..types import Address
from ..types import Component
from ..types import ComponentRole
from ..types import MessageSubSubType
from ..types import MessageSubType
from ..types import MessageType


class ResourcesDiscovery:

    def __init__(
            self,
            basicComponent: BasicComponent,
            netGateway: str = '',
            subnetMask: str = '255.255.255.0'):
        self.basicComponent = basicComponent
        self.netGateway = netGateway
        self.subnetMask = subnetMask
        self.discovered = DiscoveredManager()
        self.neighboursIP = self.generateNeighboursIP()
        # TODO: implement event listening feature
        #  Thread can be terminated when listening event happens
        self.remoteLoggerDiscovered: Event = Event()
        self.masterDiscovered: Event = Event()
        self.actorDiscovered: Event = Event()

    def checkPorts(self):
        self.checkPortOfRole(
            component=self.basicComponent.remoteLogger,
            portRange=ConfigRemoteLogger.portRange)
        self.checkPortOfRole(
            component=self.basicComponent.master,
            portRange=ConfigMaster.portRange)
        me = self.basicComponent.me
        if me.role == ComponentRole.ACTOR:
            self.checkPortOfRole(
                component=me,
                portRange=ConfigActor.portRange)
        elif me.role == ComponentRole.USER:
            self.checkPortOfRole(
                component=me,
                portRange=ConfigUser.portRange)
        elif me.role == ComponentRole.TASK_EXECUTOR:
            self.checkPortOfRole(
                component=me,
                portRange=ConfigTaskExecutor.portRange)
        return

    def checkPortOfRole(self, component: Component, portRange):
        port = component.addr[1]
        role = component.role
        if port < portRange[0] or port >= portRange[1]:
            self.basicComponent.debugLogger.error(
                '%s\'s port %d out of range [%d, %d)',
                role.value, port, portRange[0], portRange[1])
            terminate()
        return

    def discoverAndCommunicate(
            self, targetRole: ComponentRole, isNotSetInArgs: bool = False):
        if isNotSetInArgs:
            self.basicComponent.debugLogger.info(
                '%s is not set in args, will discover', targetRole.value)
        self.basicComponent.handleMessage = self.handleMessage
        self.discoverComponent(role=targetRole, block=True, showLog=True)
        if targetRole == ComponentRole.REMOTE_LOGGER:
            discovered = self.discovered.remoteLoggers
        elif targetRole == ComponentRole.MASTER:
            discovered = self.discovered.masters
        else:
            self.basicComponent.debugLogger.error(
                'Discovering does support: %s', targetRole.value)
            terminate()
            return
        addr = list(discovered)[0]
        component = Component(
            hostID='HostID',
            role=targetRole,
            addr=addr)
        if targetRole == ComponentRole.REMOTE_LOGGER:
            self.basicComponent.remoteLogger = component
        elif targetRole == ComponentRole.MASTER:
            self.basicComponent.master = component

    def discoverRemoteLoggers(self):
        self.discoverComponent(role=ComponentRole.REMOTE_LOGGER, sleepTime=1)

    def discoverMasters(self):
        self.discoverComponent(role=ComponentRole.MASTER, sleepTime=1)

    def discoverActors(self):
        self.discoverComponent(role=ComponentRole.ACTOR, sleepTime=1)

    def discoverComponent(
            self,
            role: ComponentRole,
            block: bool = False,
            showLog: bool = False,
            sleepTime: float = .1):
        if role == ComponentRole.ACTOR:
            discovered = self.discovered.actors
            event = self.actorDiscovered
        elif role == ComponentRole.MASTER:
            discovered = self.discovered.masters
            event = self.masterDiscovered
        elif role == ComponentRole.REMOTE_LOGGER:
            discovered = self.discovered.remoteLoggers
            event = self.remoteLoggerDiscovered
        else:
            return
        event.clear()
        if showLog:
            self.basicComponent.debugLogger.info(
                'Discovering %s, it may take some time', discovered.role.value)
        portRange = discovered.portRange
        if self.neighboursIP is None:
            self.neighboursIP = self.generateNeighboursIP()

        for port in range(portRange[0], portRange[1]):
            self.probe(
                addr=(self.basicComponent.addr[0], port), targetRole=role)
            for ip in self.neighboursIP:
                if event.isSet():
                    if showLog:
                        self.basicComponent.debugLogger.debug(
                            'Discovered %d %s: %s',
                            len(discovered),
                            discovered.role.value,
                            pformat(discovered))
                    return
                addr = (str(ip), port)
                # if showLog:
                #     self.basicComponent.debugLogger.debug('Probe %s', str(addr))
                if addr == self.basicComponent.addr:
                    continue
                if addr in discovered:
                    continue
                self.probe(addr=addr, targetRole=role)
                if block:
                    sleep(sleepTime)
                    continue
                sleep(sleepTime)

        if not block:
            return
        while True:
            if len(discovered):
                break
            sleep(1)

    def probe(self, addr: Address, targetRole: ComponentRole):
        destination = Component(addr=addr)
        data = {'targetRole': targetRole.value}
        self.basicComponent.sendMessage(
            messageType=MessageType.RESOURCE_DISCOVERY,
            messageSubType=MessageSubType.PROBE,
            messageSubSubType=MessageSubSubType.TRY,
            data=data,
            destination=destination,
            ignoreSocketError=True,
            showFailure=False)

    def handleMessage(self, message: MessageReceived):
        if message.typeIs(
                messageType=MessageType.RESOURCE_DISCOVERY,
                messageSubType=MessageSubType.PROBE,
                messageSubSubType=MessageSubSubType.RESULT):
            self.handleProbeResult(message=message)
        return

    def handleProbeResult(self, message: MessageReceived):
        data = message.data
        role = data['role']
        addr = message.source.addr
        if role == ComponentRole.REMOTE_LOGGER.value:
            self.remoteLoggerDiscovered.set()
            if addr in self.discovered.remoteLoggers:
                return
            self.discovered.remoteLoggers.add(addr)
        elif role == ComponentRole.MASTER.value:
            self.masterDiscovered.set()
            if addr in self.discovered.masters:
                return
            self.discovered.masters.add(addr)
        elif role == ComponentRole.ACTOR.value:
            self.actorDiscovered.set()
            if addr in self.discovered.actors:
                return
            self.discovered.actors.add(addr)
        return

    def clearDiscovered(self):
        self.discovered.remoteLoggers = set()
        self.discovered.masters = set()
        self.discovered.actors = set()

    def generateNeighboursIP(self):
        myIP = self.basicComponent.me.addr[0]
        if self.netGateway == '':
            self.netGateway = myIP[:myIP.rfind('.')] + '.0'
        network = ip_network('%s/%s' % (self.netGateway, self.subnetMask))
        return network
