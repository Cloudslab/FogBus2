import json
import os
from abc import abstractmethod
from random import randint
from threading import Lock
from time import time
from typing import Dict
from typing import List
from typing import Set
from typing import Tuple
from typing import Union

import numpy as np
from pymoo.algorithms.genetic_algorithm import GeneticAlgorithm
from pymoo.configuration import Configuration
from pymoo.factory import get_crossover
from pymoo.factory import get_mutation
from pymoo.model.crossover import Crossover
from pymoo.model.mutation import Mutation
from pymoo.model.selection import Selection
from pymoo.optimize import minimize as geneticMinimize

from .geneticProblem import GeneticProblem
from .scaler.base import NSGAScaler
from .selections.tournament import TournamentSelection
from .termination import TimeBasedSingleObjectiveDefaultTermination
from ...base import BaseScheduler
from ...types import Decision
from ....logger.allSystemPerformance import AllSystemPerformance
from ....registry.roles import User
from ....registry.roles.actor import Actor
from ....registry.roles.master import Master
from .....component.basic import BasicComponent
from .....types import Address
from .....types import Component

Configuration.show_compile_hint = False


class BaseNSGA(BaseScheduler):
    def __init__(
            self,
            knownMasters: Set[Address],
            minimumActors: int,
            schedulerName: str,
            generationNum: int,
            populationSize: int,
            basicComponent: BasicComponent,
            estimationThreadNum: int,
            isContainerMode: bool):
        BaseScheduler.__init__(
            self, schedulerName=schedulerName, isContainerMode=isContainerMode)
        self.knownMasters = knownMasters
        self.minimumActors = minimumActors
        self.basicComponent = basicComponent
        self.generationNum = generationNum
        self.populationSize = populationSize
        self.decisionHistory: Dict[str, List[Decision]] = {}
        self.geneticAlgorithm: GeneticAlgorithm = None
        self.geneticProblem: GeneticProblem = None
        self.estimationThreadNum = estimationThreadNum
        self.lock = Lock()

    def _schedule(
            self,
            user: User,
            master: Master,
            allActors: List[Actor],
            systemPerformance: AllSystemPerformance,
            isContainerMode: bool) -> Decision:
        self.joinWaiting()
        self.lock.acquire()
        self.geneticProblem = self.prepareGeneticProblem(
            user=user,
            master=master,
            allActors=allActors,
            systemPerformance=systemPerformance,
            isContainerMode=isContainerMode)
        self.geneticAlgorithm = self.prepareGeneticAlgorithm(
            application=user.application,
            estimator=self.geneticProblem.estimator)
        self.basicComponent.debugLogger.debug(
            'Scheduling using: %s', self.name)
        termination = TimeBasedSingleObjectiveDefaultTermination(
            maxTime=5,
            x_tol=1e-8,
            cv_tol=1e-6,
            f_tol=1e-6,
            nth_gen=5,
            n_last=self.generationNum % 10,
            n_max_gen=self.generationNum,
            n_max_evals=self.generationNum >> 1)
        startTime = time() * 1000
        result = geneticMinimize(
            problem=self.geneticProblem,
            algorithm=self.geneticAlgorithm,
            seed=randint(0, 100),
            termination=termination)
        schedulingTime = time() * 1000 - startTime
        decision = self.handleNSGAResult(
            user=user, result=result, schedulingTime=schedulingTime)
        self.leaveWaiting()
        self.lock.release()
        return decision

    def prepareGeneticProblem(
            self,
            user: User,
            master: Master,
            allActors: List[Actor],
            systemPerformance: AllSystemPerformance,
            isContainerMode: bool,
            *args,
            **kwargs) -> GeneticProblem:
        geneticProblem = GeneticProblem(
            user=user,
            master=master,
            systemPerformance=systemPerformance,
            allActors=allActors,
            populationSize=self.populationSize,
            threadNum=self.estimationThreadNum,
            isContainerMode=isContainerMode)
        return geneticProblem

    @abstractmethod
    def prepareGeneticAlgorithm(self, *args, **kwargs) -> GeneticAlgorithm:
        pass

    @staticmethod
    def saveEstimatingProgress(record):
        filename = './record.json'
        with open(filename, 'w+') as f:
            json.dump(record, f)
            f.close()
            try:
                os.chmod(filename, 0o666)
            except PermissionError:
                pass

    def handleNSGAResult(self, user: User, result, schedulingTime: float) -> \
            Decision:
        if len(result.X.shape) > 1:
            minIndex = np.argmin(result.F)
            cost = result.F[minIndex][0]
            indexSequence = result.X[minIndex]
            indexSequence = list(indexSequence.astype(int))
        else:
            cost = result.F[0]
            indexSequence = list(result.X.astype(int))
        indexToHostID = self.geneticProblem.estimator.mapIndexSequenceToHostIDSequence(
            indexSequence)
        self.saveEstimatingProgress(self.geneticProblem.evaluationRecords)
        decision = Decision(
            user=user,
            indexSequence=indexSequence,
            cost=cost,
            indexToHostID=indexToHostID,
            schedulingTime=schedulingTime,
            evaluationRecord=self.geneticProblem.evaluationRecords)
        if user.application.nameWithLabel not in self.decisionHistory:
            self.decisionHistory[user.application.nameWithLabel] = []
        self.decisionHistory[user.application.nameWithLabel].append(decision)
        return decision

    @staticmethod
    def getDefaultTriple() -> Tuple[Selection, Crossover, Mutation]:
        selection = TournamentSelection()
        crossover = get_crossover(
            "int_sbx",
            prob=0.5,
            eta=3.0)
        mutation = get_mutation("int_pm", eta=3.0)
        return selection, crossover, mutation

    def getBestMaster(self, user: User, masters: List[Component]) \
            -> Union[Component, None]:
        if not len(masters):
            return None
        bestMaster = masters[0]
        bestCost = self.geneticProblem.estimator.latencyRoundTrip(
            sourceComponent=user,
            destComponent=bestMaster)
        for master in masters[1:]:
            cost = self.geneticProblem.estimator.latencyRoundTrip(
                sourceComponent=user,
                destComponent=master)
            if cost >= bestCost:
                continue
            bestCost = cost
            bestMaster = master
        return bestMaster

    def prepareScaler(
            self,
            user: User,
            master: Master,
            allActors: List[Actor],
            systemPerformance: AllSystemPerformance,
            isContainerMode: bool,
            *args,
            **kwargs) -> NSGAScaler:
        if self.geneticProblem is None:
            self.geneticProblem = self.prepareGeneticProblem(
                user=user,
                master=master,
                allActors=allActors,
                systemPerformance=systemPerformance,
                isContainerMode=isContainerMode)
        scaler = NSGAScaler(
            knownMasters=self.knownMasters,
            schedulerName=self.name,
            minimumActors=self.minimumActors,
            estimationThreadNum=self.estimationThreadNum,
            estimator=self.geneticProblem.estimator,
            basicComponent=self.basicComponent)
        return scaler
