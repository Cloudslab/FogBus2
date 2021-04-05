from enum import Enum


class ComponentRole(Enum):
    REMOTE_LOGGER = 'RemoteLogger'
    MASTER = 'Master'
    ACTOR = 'Actor'
    TASK_EXECUTOR = 'TaskExecutor'
    USER = 'User'
    DEFAULT = 'Default'
