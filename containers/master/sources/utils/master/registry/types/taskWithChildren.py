from typing import Set

from .task import Task


class TaskWithChildren(Task):

    def __init__(self, name: str, token: str, childrenTokens: Set = None):
        Task.__init__(self, name, token)
        if childrenTokens is None:
            childrenTokens = set()
        self.childrenTokens = childrenTokens
