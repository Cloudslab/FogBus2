import json
import os
from collections import defaultdict
from typing import DefaultDict
from typing import Dict
from typing import List
from typing import Tuple


class Decisions:

    def __init__(
            self,
            keptDecisionsCount: int = 100):
        self.decision: Dict[str, List[Tuple[List[int], List[str]]]] = {}
        self.__filename = 'decisions.json'
        self._keptDecisionCount = keptDecisionsCount
        self._requestedAppCount: DefaultDict[str, int] = defaultdict(lambda: 0)
        self._loadFromFile()

    def update(
            self,
            appName,
            machinesIndex: List[int],
            indexToMachine: List[str]):
        self._requestedAppCount[appName] += 1
        if appName not in self.decision:
            self.decision[appName] = []
        indexes = [int(i) for i in machinesIndex]
        machines = indexToMachine
        self.decision[appName].append((indexes, machines))
        self._clean()
        self.localLogger_saveToFile()

    def _clean(self):
        totalRequest = sum(self._requestedAppCount.values())
        if totalRequest < self._keptDecisionCount // 2:
            return
        factor = self._keptDecisionCount / totalRequest
        for appName, decisions in self.decision.items():
            count = round(factor * self._requestedAppCount[appName])
            if count < len(self.decision[appName]):
                self.decision[appName] = self.decision[appName][:count]

    def good(self, appName):
        if appName not in self.decision:
            return []
        return self.decision[appName]

    def localLogger_saveToFile(self):
        f = open(self.__filename, 'w+')
        json.dump(self.decision, f)
        f.close()

    def _loadFromFile(self):
        if os.path.exists(self.__filename):
            f = open(self.__filename, 'r')
            content = json.load(f)
            f.close()
            self.decision = defaultdict(List[List[int]], content)
            for appName, records in self.decision.items():
                self._requestedAppCount[appName] = len(records)
            self._clean()
