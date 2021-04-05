from pprint import pformat
from typing import Dict
from typing import List

from ...registry.roles import User
from ....types import SerializableDictionary


class Decision(SerializableDictionary):

    def __init__(
            self,
            user: User,
            indexSequence: List[str],
            indexToHostID: Dict[str, str],
            schedulingTime: float,
            cost: float = -1,
            evaluationRecord: List[float] = None):
        if evaluationRecord is None:
            self.evaluationRecord = []
        else:
            self.evaluationRecord = evaluationRecord
        self.schedulingTime = schedulingTime
        self.user = user
        self.indexToHostID = indexToHostID
        self.indexSequence = indexSequence
        self.cost: float = cost

    def __repr__(self):
        represent = '%s, %.2f' % (self.user.application.nameWithLabel,
                                  self.cost)
        return represent

    def __str__(self):
        return pformat(
            object=self.__dict__,
            indent=3)

    def hostIDSequence(self) -> List[str]:
        hostIDSequence = [self.indexToHostID[i] for i in self.indexSequence]
        return hostIDSequence

    @staticmethod
    def fromDict(inDict: Dict):
        decision = Decision(
            user=inDict['user'],
            indexSequence=inDict['indexSequence'],
            indexToHostID=inDict['indexToHostID'],
            schedulingTime=inDict['schedulingTime'],
            evaluationRecord=inDict['evaluationRecord'],
            cost=inDict['cost'])
        return decision

    def toDict(self) -> Dict:
        inDict = {
            'user': self.user.toDict(),
            'indexSequence': self.indexSequence,
            'indexToHostID': self.indexToHostID,
            'evaluationRecord': self.evaluationRecord,
            'schedulingTime': self.schedulingTime,
            'cost': self.cost}
        return inDict
