from typing import Set

from ..base import Task


class TaskWithDependency(Task):

    def __init__(
            self,
            name: str,
            parents: Set[Task] = None,
            children: Set[Task] = None):
        Task.__init__(
            self,
            name=name)
        if parents is None:
            parents = set()
        if children is None:
            children = set()
        self.parents = parents
        self.children = children
