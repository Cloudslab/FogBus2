from abc import abstractmethod
from typing import Dict


class SerializableDictionary:
    @staticmethod
    @abstractmethod
    def fromDict(inDict: Dict):
        pass

    @abstractmethod
    def toDict(self) -> Dict:
        pass
