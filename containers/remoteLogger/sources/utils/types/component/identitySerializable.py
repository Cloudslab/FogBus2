from typing import Dict

from .identity import ComponentIdentity
from .role import ComponentRole
from ..basic import SerializableDictionary


class Component(ComponentIdentity, SerializableDictionary):

    @staticmethod
    def fromDict(inDict: Dict):
        addrInList = inDict['addr']
        identity = Component(
            role=ComponentRole(inDict['role']),
            componentID=inDict['componentID'],
            addr=(addrInList[0], addrInList[1]),
            name=inDict['name'],
            nameLogPrinting=inDict['nameLogPrinting'],
            nameConsistent=inDict['nameConsistent'],
            hostID=inDict['hostID'])
        return identity

    def toDict(self) -> Dict:
        inDict = {
            'role': self.role.value,
            'componentID': self.componentID,
            'addr': list(self.addr),
            'name': self.name,
            'nameLogPrinting': self.nameLogPrinting,
            'nameConsistent': self.nameConsistent,
            'hostID': self.hostID}
        return inDict
