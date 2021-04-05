from typing import Tuple

from .actor import Actor
from .user import User
from ...application.base import Application
from ...application.task.base import Task
from ....types import Component
from ....types.component.role import ComponentRole

Names = Tuple[str, str, str]


class NameFactory:

    def __init__(self, nameLogPrinting: str):
        self.nameLogPrinting = nameLogPrinting

    def nameActor(self, source: Component, actorID: str) -> Names:
        name = self.actorName()
        nameLogPrinting = self.actorNameLogPrinting(
            name=name, actorID=actorID, source=source)
        nameConsistent = self.actorNameConsistent(name, source)

        return name, nameLogPrinting, nameConsistent

    def nameUser(
            self, source: Component, userID: str, application: Application) \
            -> Names:
        name = self.userName(application, application.label)
        nameLogPrinting = self.userNameLogPrinting(
            name=name, userID=userID, source=source)
        nameConsistent = self.userNameConsistent(name, source)
        return name, nameLogPrinting, nameConsistent

    def nameTaskExecutor(self, source: Component, taskExecutorID: str,
                         task: Task, user: User, actor: Actor) -> Names:
        name = self.taskExecutorName(task, user)
        nameLogPrinting = self.taskExecutorNameLogPrinting(
            user=user, name=name, taskExecutorID=taskExecutorID, source=source)
        nameConsistent = self.taskExecutorNameConsistent(
            name, actor)
        return name, nameLogPrinting, nameConsistent

    @staticmethod
    def actorName() -> str:
        return ComponentRole.ACTOR.value

    def actorNameLogPrinting(
            self,
            name: str,
            actorID: str,
            source: Component) -> str:
        nameLogPrinting = '%s-%s_%s-%d_%s' % (
            name,
            actorID,
            source.addr[0],
            source.addr[1],
            self.nameLogPrinting)
        return nameLogPrinting

    @staticmethod
    def actorNameConsistent(
            name: str, source: Component) -> str:
        nameConsistent = '%s_%s' % (name, source.hostID)
        return nameConsistent

    @staticmethod
    def userName(application: Application, label: str) -> str:
        name = '%s-%s-%s' % (ComponentRole.USER.value, application.name, label)
        return name

    def userNameLogPrinting(
            self,
            name: str,
            userID: str,
            source: Component) -> str:
        nameLogPrinting = '%s-%s_%s-%d_%s' % (
            name,
            userID,
            source.addr[0],
            source.addr[1],
            self.nameLogPrinting)
        return nameLogPrinting

    @staticmethod
    def userNameConsistent(
            name: str,
            source: Component) -> str:
        nameConsistent = '%s_%s' % (name, source.hostID)
        return nameConsistent

    @staticmethod
    def taskExecutorName(task: Task, user: User) -> str:
        name = '%s-%s-%s' % (ComponentRole.TASK_EXECUTOR.value,
                             task.name,
                             user.application.label)
        return name

    def taskExecutorNameLogPrinting(
            self,
            user: User,
            name: str,
            taskExecutorID: str,
            source: Component) -> str:
        nameLogPrinting = '%s-%s_%s-%s_%s-%d_%s' % (
            name,
            taskExecutorID,
            user.role.value,
            user.componentID,
            source.addr[0],
            source.addr[1],
            self.nameLogPrinting)
        return nameLogPrinting

    @staticmethod
    def taskExecutorNameConsistent(
            name: str,
            actor: Actor) -> str:
        nameConsistent = '%s_%s' % (name, actor.hostID)
        return nameConsistent
