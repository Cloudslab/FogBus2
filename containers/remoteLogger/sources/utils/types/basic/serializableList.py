from abc import abstractmethod
from typing import List


class SerializableList:
    @staticmethod
    @abstractmethod
    def fromList(inList: List):
        pass

    @abstractmethod
    def toList(self) -> List:
        pass
