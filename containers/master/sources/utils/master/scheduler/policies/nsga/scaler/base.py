from time import sleep
from typing import List
from typing import Set
from typing import Union

from ....estimator import Estimator
from ....baseScaler import Scaler
from ....tools import assessResourceScore
from .....registry.roles import Actor
from .....registry.roles import User
from ......component.basic import BasicComponent
from ......types import Address
from ......types import Component
from ......types import ComponentRole
from ......types import MessageSubType
from ......types import MessageType


class NSGAScaler(Scaler):

    def __init__(
            self,
            knownMasters: Set[Address],
            schedulerName: str,
            estimationThreadNum: int,
            minimumActors: int,
            estimator: Estimator,
            basicComponent: BasicComponent):
        Scaler.__init__(
            self,
            schedulerName=schedulerName,
            minimumActors=minimumActors,
            basicComponent=basicComponent)
        self.knownMasters = knownMasters
        self.estimator = estimator
        self.estimationThreadNum = estimationThreadNum

    def scale(self, user: User, actors: List[Actor]) -> Union[Component, None]:
        self.basicComponent.debugLogger.debug(
            'Scaling for user: %s', user.nameLogPrinting)
        filteredActors = []
        for actor in actors:
            if actor.addr[0] == self.basicComponent.addr[0]:
                continue
            filteredActors.append(actor)
        if len(filteredActors) == 0:
            self.warnUser(user)
            self.basicComponent.debugLogger.debug(
                'No available %s to scale', ComponentRole.ACTOR.value)
            return None
        bestActor = filteredActors[0]
        bestScore = assessResourceScore(bestActor.actorResources)
        minLatency = self.estimator.latencyRoundTrip(
            sourceComponent=user,
            destComponent=bestActor)
        for actor in filteredActors[1:]:
            latency = self.estimator.latencyRoundTrip(
                sourceComponent=user,
                destComponent=actor)
            if latency > minLatency:
                continue
            score = assessResourceScore(actor.actorResources)
            if latency == minLatency and score < bestScore:
                continue
            bestScore = score
            bestActor = actor
            minLatency = latency

        newMaster = self.sendInitNewMasterMsg(bestActor)
        return newMaster

    def sendInitNewMasterMsg(self, actor: Actor) -> Component:
        data = {
            'schedulerName': self.schedulerName,
            'minimumActors': self.minimumActors,
            'estimationThreadNum': self.estimationThreadNum}
        self.basicComponent.sendMessage(
            messageType=MessageType.SCALING,
            messageSubType=MessageSubType.INIT_NEW_MASTER,
            data=data,
            destination=actor)
        self.basicComponent.debugLogger.debug(
            'Send init new master msg to %s', actor.nameLogPrinting)
        while True:
            if not len(self.knownMasters):
                sleep(.05)
                continue
            break
        masterAddr = list(self.knownMasters)[0]
        master = Component(addr=masterAddr)
        return master
