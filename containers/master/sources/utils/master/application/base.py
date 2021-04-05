from typing import Dict
from typing import List

from .task.dependency.base import TaskWithDependency
from ...types import SerializableDictionary


class Application(SerializableDictionary):
    def __init__(
            self,
            name: str,
            tasksWithDependency: Dict[str, TaskWithDependency],
            entryTasks: List[TaskWithDependency],
            label: str = ''):
        self.name = name
        self.tasksWithDependency = tasksWithDependency
        self.entryTasks = entryTasks
        self.label = label
        self.nameWithLabel = name
        self.taskNameList: List[str] = []
        self.entryTaskNameList: List[str] = []
        self.refreshAttributes()

    def __repr__(self):
        if self.label == '':
            return 'Application(name = %s)' % self.name
        return 'Application(name = %s)' % self.nameWithLabel

    def refreshAttributes(self):
        taskList = list(self.tasksWithDependency.keys())
        if self.label == '':
            self.taskNameList = taskList
            self.entryTaskNameList = [task.name for task in self.entryTasks]
            return
        self.nameWithLabel = '%s-%s' % (self.name, self.label)
        self.taskNameList = ['' for _ in range(len(taskList))]
        for i, taskName in enumerate(taskList):
            self.taskNameList[i] = '%s-%s' % (taskName, self.label)
        entryTaskNameList = ['%s-%s' % (task.name, self.label) for task in
                             self.entryTasks]
        self.entryTaskNameList = entryTaskNameList

    @staticmethod
    def fromDict(inDict: Dict):
        application = Application(
            name=inDict['name'],
            tasksWithDependency=inDict['tasksWithDependency'],
            entryTasks=inDict['entryTasks'],
            label=inDict['label'])
        return application

    def toDict(self) -> Dict:
        inDict = {
            'name': self.name,
            'tasksWithDependency': self.tasksWithDependency,
            'entryTasks': self.entryTasks,
            'label': self.label, }
        return inDict

    def copy(self, withLabel: str = ''):
        inDict = self.toDict()
        inDict['label'] = withLabel
        duplicatedApplication = self.fromDict(inDict)
        return duplicatedApplication
