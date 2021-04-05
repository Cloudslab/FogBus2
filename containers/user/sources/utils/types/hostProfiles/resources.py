from typing import Dict

from .cpu import CPU
from .memory import Memory
from ..basic import AutoDictionary


class Resources(AutoDictionary):

    def __init__(self,
                 cpu: CPU = CPU(),
                 memory: Memory = Memory()):
        self.cpu = cpu
        self.memory = memory

    def toDict(self):
        inDict = {
            'cpu': self.cpu.toDict(),
            'memory': self.memory.toDict()}
        return inDict

    @staticmethod
    def fromDict(inDict: Dict):
        profiles = Resources(
            cpu=CPU.fromDict(inDict['cpu']),
            memory=Memory.fromDict(inDict['memory']))
        return profiles
