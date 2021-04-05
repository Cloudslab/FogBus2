from typing import List
from typing import Set

from pymoo.algorithms.genetic_algorithm import GeneticAlgorithm
from pymoo.algorithms.nsga2 import NSGA2 as NSGA2_
from pymoo.model.evaluator import Evaluator as Evaluator_
from pymoo.model.population import Population

from .base import BaseNSGA
from ...estimator import Estimator
from .tools.randomPopulation import randomPopulation
from ....application.base import Application
from .....component.basic import BasicComponent
from .....types import Address


class OHNSGA(BaseNSGA):

    def __init__(
            self,
            knownMasters: Set[Address],
            minimumActors: int,
            generationNum: int,
            populationSize: int,
            basicComponent: BasicComponent,
            estimationThreadNum: int,
            isContainerMode: bool,
            historyRatio: float = .5):
        BaseNSGA.__init__(
            self,
            knownMasters=knownMasters,
            minimumActors=minimumActors,
            schedulerName='OHNSGA',
            generationNum=generationNum,
            populationSize=populationSize,
            basicComponent=basicComponent,
            estimationThreadNum=estimationThreadNum,
            isContainerMode=isContainerMode)
        self.historyRatio = historyRatio

    def prepareGeneticAlgorithm(
            self, application: Application, estimator: Estimator) \
            -> GeneticAlgorithm:
        selection, crossover, mutation = self.getDefaultTriple()
        initPopulation = self.generateInitPopulation(
            application=application, estimator=estimator)
        geneticAlgorithm = NSGA2_(
            pop_size=self.populationSize,
            sampling=initPopulation,
            crossover=crossover,
            mutation=mutation,
            selection=selection,
            eliminate_duplicates=False)
        return geneticAlgorithm

    def generateInitPopulation(
            self, application: Application, estimator: Estimator):
        if application.nameWithLabel not in self.decisionHistory:
            decisionHistory = []
        else:
            decisionHistory = self.decisionHistory[application.nameWithLabel]
        numDecisionHistory = len(decisionHistory)
        numDecisionToUse = int(numDecisionHistory * self.historyRatio)
        decisionHistory = decisionHistory[-numDecisionToUse:]
        indexSequences = self.understandHistory(
            decisionHistory=decisionHistory,
            estimator=estimator)
        initPopulation = self.fillWithRandomIndexSequence(indexSequences)
        return initPopulation

    @staticmethod
    def understandHistory(decisionHistory, estimator):
        indexSequences = [[] for _ in range(len(decisionHistory))]
        for i, decision in enumerate(decisionHistory):
            hostIDSequence = decision.hostIDSequence()
            indexSequences[i] = \
                estimator.mapHostIDSequenceToIndexSequence(hostIDSequence)
        return indexSequences

    def fillWithRandomIndexSequence(self, indexSequences: List[List[int]]):
        upperBounds = self.geneticProblem.upperBound
        lowerBounds = [0 for _ in range(len(upperBounds))]
        variableNum = self.geneticProblem.variableNum
        indexSequencesRandom = randomPopulation(
            lowerBounds=lowerBounds,
            upperBounds=upperBounds,
            variableNum=variableNum,
            populationSize=self.populationSize)

        for i, indexSequence in enumerate(indexSequences):
            indexSequencesRandom[i] = indexSequence

        population = Population.new("X", indexSequencesRandom)
        Evaluator_().eval(self.geneticProblem, population)
        for i in range(len(population)):
            population[i].CV = population[i].F
        return population
