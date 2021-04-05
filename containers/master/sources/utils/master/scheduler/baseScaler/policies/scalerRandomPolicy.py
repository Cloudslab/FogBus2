from random import randint
from typing import List

from ..base import Scaler
from ....registry.roles.actor import Actor
from ....registry.roles.user import User
from .....types import Component as ActorComponent


class ScalerRandomPolicy(Scaler):

    def scale(self, *args, **kwargs) -> ActorComponent:
        """
        :param args:
        :param kwargs:
        :return: an Actor
        """
        # User and all Actors list will be passed in
        user: User = kwargs['user']
        allActors: List[Actor] = kwargs['allActors']

        # Get actors number and randomly pick one to scale
        actorsNum = len(allActors)
        randomActor = allActors[randint(0, actorsNum - 1)]
        return randomActor
