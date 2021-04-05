from abc import abstractmethod

from ...registry.roles import User
from ....component.basic import BasicComponent
from ....types import Component
from ....types import ComponentRole
from ....types import MessageSubType
from ....types import MessageType


class Scaler:

    def __init__(
            self,
            schedulerName: str,
            minimumActors: int,
            basicComponent: BasicComponent):
        self.minimumActors = minimumActors
        self.schedulerName = schedulerName
        self.basicComponent = basicComponent

    @abstractmethod
    def scale(self, *args, **kwargs) -> Component:
        raise NotImplementedError

    def notifyUser(self, user: User, anotherMaster: Component):
        data = {'masterAddr': list(anotherMaster.addr)}
        self.basicComponent.sendMessage(
            messageType=MessageType.SCALING,
            messageSubType=MessageSubType.CONNECT_TO_NEW_MASTER,
            data=data,
            destination=user)

    def warnUser(self, user: User):
        self.basicComponent.sendMessage(
            messageType=MessageType.ACKNOWLEDGEMENT,
            messageSubType=MessageSubType.NO_ACTOR,
            data={},
            destination=user)
        self.basicComponent.debugLogger.debug(
            'Warn %s there is no %s: %s',
            ComponentRole.USER.value,
            ComponentRole.ACTOR.value,
            user.nameLogPrinting)
