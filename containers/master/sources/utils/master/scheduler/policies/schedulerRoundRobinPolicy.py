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


class SchedulerRoundRobinPolicy(SchedulerPolicy):
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
        super().__init__('RoundRobin', isContainerMode, *args, **kwargs)

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
        # Assign in Round-robin style
        for i, _ in enumerate(indexSequence):
            actorIndex = i % actorsNum
            indexSequence[i] = str(actorIndex)
            actor = allActors[actorIndex]
            indexToHostID[str(actorIndex)] = actor.hostID
        schedulingTime = (time() - startTime) * 1000

        # Create a decision object and return
        decision = Decision(
            user=user,
            indexSequence=indexSequence,
            indexToHostID=indexToHostID,
            schedulingTime=schedulingTime
        )
        # Estimate the cost
        decision.cost = self.estimateCost(decision, **kwargs)
        return decision

    @staticmethod
    def estimateCost(decision: Decision, **kwargs) -> float:
        # We use estimator in NAGA as an Example
        # You may develop your own with the following used values
        from ..estimator.estimator import Estimator
        # Get necessary params from the key args
        user = kwargs['user']
        master = kwargs['master']
        systemPerformance = kwargs['systemPerformance']
        allActors = kwargs['allActors']
        isContainerMode = kwargs['isContainerMode']
        # Init the estimator
        estimator = Estimator(
            user=user,
            master=master,
            systemPerformance=systemPerformance,
            allActors=allActors,
            isContainerMode=isContainerMode)
        indexSequence = [int(i) for i in decision.indexSequence]
        # Estimate the cost
        estimatedCost = estimator.estimateCost(indexSequence)
        return estimatedCost

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
