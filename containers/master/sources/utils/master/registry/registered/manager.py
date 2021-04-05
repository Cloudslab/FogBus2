from typing import Dict
from typing import Set

from .actors import RegisteredActors
from .masters import RegisteredMasters
from .taskExecutors import RegisteredTaskExecutors
from .users import RegisteredUsers
from ..roles.taskExecutor import TaskExecutor


class RegisteredManager:
    def __init__(self):
        self.actors: RegisteredActors = RegisteredActors()
        self.users = RegisteredUsers()
        self.taskExecutors = RegisteredTaskExecutors()
        self.masters = RegisteredMasters()
        # TODO: Thread Safe
        self.coolTaskExecutors: Dict[str, Dict[str, Set[TaskExecutor]]] = {}
