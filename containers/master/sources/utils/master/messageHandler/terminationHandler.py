from .acknowledgementHandler import AcknowledgementHandler
from .tools import terminateMessage
from ..registry.base import Registry
from ...component.basic import BasicComponent
from ...connection import HandlerReturn
from ...connection import MessageReceived
from ...types import ComponentRole


class TerminationHandler:

    def __init__(
            self,
            basicComponent: BasicComponent,
            registry: Registry,
            acknowledgementHandler: AcknowledgementHandler):
        self.basicComponent = basicComponent
        self.registry = registry
        self.acknowledgementHandler = acknowledgementHandler

    def handleExit(self, message: MessageReceived) -> HandlerReturn:
        data = message.data
        source = message.source
        componentID = source.componentID
        registeredManager = self.registry.registeredManager
        responseData = None
        if data['reason'] != 'Manually interrupted.':
            self.basicComponent.debugLogger.info(
                '%s at %s exit with reason: %s',
                source.nameLogPrinting,
                str(source.addr), data['reason'])
        if source.role is ComponentRole.USER:
            self.basicComponent.debugLogger.debug(
                'Deregister: %s', source.nameLogPrinting)
            if componentID in registeredManager.users:
                user = registeredManager.users[componentID]
                self.registry.deregisterUser(user)
                nameConsistent = user.nameConsistent
                packetSize = self.basicComponent.receivedPacketSize[
                    nameConsistent]
                responseData = {'packetSize': packetSize.median()}
            else:
                responseData = {'packetSize': -1}
        elif source.role is ComponentRole.TASK_EXECUTOR:
            if componentID in registeredManager.taskExecutors:
                taskExecutor = registeredManager.taskExecutors[componentID]
                self.registry.deregisterTaskExecutor(taskExecutor)
        elif source.role is ComponentRole.ACTOR:
            if componentID in registeredManager.actors:
                actor = registeredManager.actors[componentID]
                self.registry.deregisterActor(actor)
        return terminateMessage(
            component=source, reason='User cancelled', data=responseData)
    