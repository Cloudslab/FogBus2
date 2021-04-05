from typing import Dict

from .task import Task


class TaskLabeled(Task):

    def __init__(self, name: str, token: str, label: str = ''):
        Task.__init__(self, name=name, token=token)
        self.label = label
        self.nameLabeled = self.name
        if self.label == '':
            return
        self.nameLabeled = '%s-%s' % (self.name, self.label)

    @staticmethod
    def fromDict(inDict: Dict):
        if 'label' not in inDict:
            inDict['label'] = ''
        taskWithLabel = TaskLabeled(
            name=inDict['name'],
            token=inDict['token'],
            label=inDict['label'])
        return taskWithLabel

    def toDict(self) -> Dict:
        inDict = {
            'name': self.name,
            'token': self.token,
            'label': self.label}
        return inDict
