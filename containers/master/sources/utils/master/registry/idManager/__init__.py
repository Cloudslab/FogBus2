from .base import BaseIDManager


class IDManager:
    actor: BaseIDManager = BaseIDManager()
    user: BaseIDManager = BaseIDManager()
    taskExecutor: BaseIDManager = BaseIDManager()
