from typing import Set

from pymoo.algorithms.genetic_algorithm import GeneticAlgorithm
from pymoo.algorithms.nsga3 import NSGA3 as NSGA3_
from pymoo.factory import get_reference_directions

from .base import BaseNSGA
from ...estimator import Estimator
from .tools.randomPopulation import randomPopulation
from ....application.base import Application
from .....component.basic import BasicComponent
from .....types import Address


class NSGA3(BaseNSGA):

    def __init__(
            self,
            knownMasters: Set[Address],
            minimumActors: int,
            generationNum: int,
            populationSize: int,
            basicComponent: BasicComponent,
            estimationThreadNum: int,
            isContainerMode: bool,
            historyRatio: float = .5, ):
        BaseNSGA.__init__(
            self,
            knownMasters=knownMasters,
            minimumActors=minimumActors,
            schedulerName='NSGA3',
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
        initPopulation = self.generateInitPopulation()
        refDirs = get_reference_directions("das-dennis", 1, n_partitions=1)
        geneticAlgorithm = NSGA3_(
            pop_size=self.populationSize,
            sampling=initPopulation,
            crossover=crossover,
            mutation=mutation,
            ref_dirs=refDirs,
            eliminate_duplicates=False)

        return geneticAlgorithm

    def generateInitPopulation(self):
        upperBounds = self.geneticProblem.upperBound
        lowerBounds = [0 for _ in range(len(upperBounds))]
        variableNum = self.geneticProblem.variableNum
        initPopulation = randomPopulation(
            lowerBounds=lowerBounds,
            upperBounds=upperBounds,
            variableNum=variableNum,
            populationSize=self.populationSize)
        return initPopulation
