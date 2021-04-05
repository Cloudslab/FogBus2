from typing import Dict

from ....types.basic.serializableDictionary import SerializableDictionary


class Task(SerializableDictionary):

    def __init__(self, name: str, token: str):
        self.name = name
        self.token = token

    @staticmethod
    def fromDict(inDict: Dict):
        task = Task(
            name=inDict['name'],
            token=inDict['token'])
        return task

    def toDict(self) -> Dict:
        inDict = {
            'name': self.name,
            'token': self.token}
        return inDict
