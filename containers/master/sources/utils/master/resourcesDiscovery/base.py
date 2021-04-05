from time import sleep
from typing import Set

from ..registry.base import Registry
from ...component import BasicComponent
from ...resourceDiscovery import ResourcesDiscovery
from ...types import Address
from ...types.component.identitySerializable import \
    Component
from ...types.component.role import ComponentRole
from ...types.message.subType import MessageSubType
from ...types.message.type import MessageType


class MasterResourcesDiscovery(ResourcesDiscovery):

    def __init__(
            self,
            registry: Registry,
            basicComponent: BasicComponent,
            createdByIP: str,
            createdByPort: int,
            netGateway: str = '',
            subnetMask: str = '255.255.255.0'):
        ResourcesDiscovery.__init__(
            self,
            basicComponent=basicComponent,
            netGateway=netGateway,
            subnetMask=subnetMask)
        self.registry = registry
        self.neighboursIP = None
        self.createdBy = Component(
            role=ComponentRole.MASTER,
            addr=(createdByIP, createdByPort))
        self.isScaled = False
        if self.createdBy.addr[0] != '':
            self.isScaled = True

    def requestLoggerFrom(self, anotherMaster: Component):
        # TODO: make the port flexible
        self.basicComponent.debugLogger.info(
            'Request logger from %s' % str(anotherMaster.addr))
        self.getActorsAddrFrom(anotherMaster)
        self.getProfilesFrom(anotherMaster)

    def getActorAddrFromOtherMasters(self):
        for addr in self.discovered.masters:
            if addr == self.basicComponent.addr:
                continue
            component = Component(addr=addr)
            self.getActorsAddrFrom(component)
            sleep(1)

    def getActorsAddrFrom(self, anotherMaster: Component):
        self.basicComponent.sendMessage(
            messageType=MessageType.RESOURCE_DISCOVERY,
            messageSubType=MessageSubType.REQUEST_ACTORS_INFO,
            data={},
            destination=anotherMaster,
            ignoreSocketError=True,
            showFailure=False)

    def getProfilesFrom(self, component: Component):
        self.basicComponent.sendMessage(
            messageType=MessageType.SCALING,
            messageSubType=MessageSubType.GET_PROFILES,
            data={},
            destination=component)

    def advertiseMeToActors(self):
        actors = self.discovered.actors
        if not len(actors):
            return
        registeredActorSet = self.getRegisteredActorsAddr()
        for addr in actors:
            if addr in registeredActorSet:
                continue
            self.basicComponent.sendMessage(
                messageType=MessageType.RESOURCE_DISCOVERY,
                messageSubType=MessageSubType.ADVERTISE_MASTER,
                data={},
                destination=Component(addr=addr))
        return

    def getRegisteredActorsAddr(self) -> Set[Address]:
        actorsAddr = set([])
        actors = self.registry.registeredManager.actors.copyAll()
        for actor in actors:
            if actor.addr in actorsAddr:
                continue
            actorsAddr.add(actor.addr)
        return actorsAddr
