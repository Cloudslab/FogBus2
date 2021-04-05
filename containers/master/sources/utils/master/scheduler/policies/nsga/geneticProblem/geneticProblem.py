from queue import Queue
from threading import Event
from threading import Thread
from typing import Dict
from typing import List
from typing import Tuple

import numpy as np
from pymoo.model.problem import Problem

from ....estimator import Estimator
from .....logger.allSystemPerformance import AllSystemPerformance
from .....registry.roles import Actor
from .....registry.roles import Master
from .....registry.roles import User
from ......types import ComponentRole


class GeneticProblem(Problem):

    def __init__(
            self,
            user: User,
            master: Master,
            systemPerformance: AllSystemPerformance,
            allActors: List[Actor],
            isContainerMode: bool,
            populationSize: int,
            threadNum: int = 4):
        self.threadNum = threadNum
        self.populationSize = populationSize
        self.individualEvents = [Event() for _ in range(self.populationSize)]
        self.individualQueue: Queue[Tuple[int, List[int], Event]] = Queue()
        self.result = np.asarray([.0 for _ in range(self.populationSize)])
        self.runEvaluationThreadPool(threadNum=threadNum)

        self.estimator = Estimator(
            user=user,
            master=master,
            systemPerformance=systemPerformance,
            allActors=allActors,
            isContainerMode=isContainerMode)

        self.choicesEachVariable = [len(actors) - 1 for actors in
                                    self.estimator.actorsByTaskName.values()]
        self.variableNum = len(self.estimator.taskList)
        self.lowerBound = [0 for _ in range(self.variableNum)]
        self.upperBound = self.choicesEachVariable
        Problem.__init__(
            self,
            xl=self.lowerBound,
            xu=self.upperBound,
            n_obj=1,
            n_var=self.variableNum,
            type_var=np.int)
        self.evaluationRecords = []

    def getChoicesEachVariable(self, actorsByTaskName: Dict[str, Actor]) \
            -> List[int]:
        choicesEachVariable = [0 for _ in range(len(actorsByTaskName))]
        i = 0
        for taskName, actors in self.estimator.actorsByTaskName.items():
            num = len(actors)
            if num <= 0:
                Exception(
                    'There is no %s has image for %s' % (
                        ComponentRole.ACTOR.value, taskName))
            choicesEachVariable[i] = num - 1
            i += 1
        return choicesEachVariable

    def runEvaluationThreadPool(self, threadNum: int = 4):
        for i in range(threadNum):
            Thread(target=self.estimationThread).start()

    def estimationThread(self):
        while True:
            i, individual, event = self.individualQueue.get()
            self.result[i] = self.estimator.estimateCost(individual)
            event.set()

    def _evaluate(self, indexSequenceList, out, *args, **kwargs):
        for i, indexSequence in enumerate(indexSequenceList):
            self.individualQueue.put(
                (i, indexSequence, self.individualEvents[i]))
        for event in self.individualEvents:
            event.wait()
            event.clear()
        out['F'] = self.result
        self.evaluationRecords.append(min(out['F']))
