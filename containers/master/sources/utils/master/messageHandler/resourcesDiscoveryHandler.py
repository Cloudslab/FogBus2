from ..resourcesDiscovery import MasterResourcesDiscovery
from ...component import BasicComponent
from ...connection import MessageReceived
from ...types import MessageSubType
from ...types import MessageType


class ResourcesDiscoveryHandler:

    def __init__(
            self,
            basicComponent: BasicComponent,
            resourcesDiscovery: MasterResourcesDiscovery):
        self.basicComponent = basicComponent
        self.resourcesDiscovery = resourcesDiscovery

    def handleActorsAddr(self, message: MessageReceived):
        """
        :param message:
        :return: Actors' addr registered here
        """
        source = message.source
        actorsAddrSet = self.resourcesDiscovery.getRegisteredActorsAddr()
        if not len(actorsAddrSet):
            return

        data = {'actorsAddrResult': list(actorsAddrSet)}
        self.basicComponent.sendMessage(
            messageType=MessageType.RESOURCE_DISCOVERY,
            messageSubType=MessageSubType.ACTORS_INFO,
            data=data,
            destination=source)
        from pprint import pformat
        self.basicComponent.debugLogger.debug(
            'Send actorsAddrResult to %s:\n %s',
            source.nameLogPrinting,
            pformat(data))

    def handleActorsAddrResult(self, message: MessageReceived):
        actorsAddr = message.data['actorsAddrResult']
        for addr in actorsAddr:
            if addr in self.resourcesDiscovery.discovered.actors:
                return
            self.resourcesDiscovery.discovered.actors.add(addr)

        from pprint import pformat
        self.basicComponent.debugLogger.debug(
            'Got actorsAddrResult from %s:\n %s',
            message.source.nameLogPrinting,
            pformat(actorsAddr))
        self.resourcesDiscovery.advertiseMeToActors()
        return
