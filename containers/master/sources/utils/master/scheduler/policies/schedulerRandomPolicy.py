from random import randint
from time import time
from typing import List
from typing import Union

from ..base import BaseScheduler as SchedulerPolicy
from ..baseScaler.base import Scaler
from ..baseScaler.policies.scalerRandomPolicy import ScalerRandomPolicy
from ..types import Decision
from ...registry.roles.actor import Actor
from ...registry.roles.user import User
from ....types import Component


class SchedulerRandomPolicy(SchedulerPolicy):
    def __init__(
            self,
            isContainerMode: bool,
            *args,
            **kwargs):
        """
        :param isContainerMode: Whether this component is running in container
        :param args:
        :param kwargs:
        """
        super().__init__('Random', isContainerMode, *args, **kwargs)

    def _schedule(self, *args, **kwargs) -> Decision:
        """
        :param args:
        :param kwargs:
        :return: A decision object
        """
        user: User = kwargs['user']
        allActors: List[Actor] = kwargs['allActors']
        # Get what tasks are required
        taskNameList = user.application.taskNameList

        actorsNum = len(allActors)
        startTime = time()
        indexSequence = ['' for _ in range(len(taskNameList))]
        indexToHostID = {}
        # Randomly assign Actors
        for i, task in enumerate(taskNameList):
            randomActorIndex = randint(0, actorsNum)
            indexSequence[i] = str(randomActorIndex)

            actor = allActors[randomActorIndex]
            indexToHostID[str(randomActorIndex)] = actor.hostID
        schedulingTime = (time() - startTime) * 1000

        # Create a decision object and return
        decision = Decision(
            user=user,
            indexSequence=indexSequence,
            indexToHostID=indexToHostID,
            schedulingTime=schedulingTime
        )
        return decision

    def getBestMaster(self, *args, **kwargs) -> Union[Component, None]:
        """

        :param args:
        :param kwargs:
        :return: A Master used to ask user to request when this Master is busy
        """
        user: User = kwargs['user']
        knownMasters: List[Component] = kwargs['knownMasters']
        mastersNum = len(knownMasters)
        if mastersNum == 0:
            return None
        return knownMasters[randint(0, mastersNum - 1)]

    def prepareScaler(self, *args, **kwargs) -> Scaler:
        # Create a scaler object and return
        scaler = ScalerRandomPolicy(*args, **kwargs)
        return scaler
