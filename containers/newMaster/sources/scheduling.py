import numpy as np
import autograd.numpy as anp

from random import randint, shuffle
from pymoo.algorithms.genetic_algorithm import GeneticAlgorithm
from pymoo.algorithms.ctaea import CTAEA as CTAEA_
from pymoo.algorithms.nsga3 import NSGA3 as NSGA3_
from pymoo.algorithms.nsga2 import NSGA2 as NSGA2_
from pymoo.factory import get_reference_directions
from pymoo.optimize import minimize
from abc import abstractmethod
from pymoo.model.problem import Problem
from typing import Dict, List, Tuple
from dependencies import loadDependencies, Task, Application
from copy import deepcopy
from collections import defaultdict
from pprint import pformat
from pymoo.configuration import Configuration
from resourcesInfo import ResourcesInfo
from hashlib import sha256

Configuration.show_compile_hint = False
EdgesByName = Dict[str, List[str]]


def genMachineIDForTaskHandler(
        userMachineID: str,
        workerMachineID: str,
        machineName: str):
    info = machineName
    info += userMachineID
    info += workerMachineID
    return sha256(info.encode('utf-8')).hexdigest()


class Decision:

    def __init__(
            self,
            machines: Dict[str, str],
            edgePackageSize: float,
            edgeDelay: float,
            computingCost: float,
            varReciprocal: float,
    ):
        self.machines: Dict[str, str] = machines
        self.edgePackageSize: float = edgePackageSize
        self.edgeDelay: float = edgeDelay
        self.computingCost: float = computingCost
        self.varReciprocal: float = varReciprocal

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return pformat(
            object=self.__dict__,
            indent=3)


class Scheduler:

    def __init__(
            self,
            name: str,
            medianPackageSize: Dict[str, Dict[str, float]],
            medianDelay: Dict[str, Dict[str, float]],
            medianProcessTime: Dict[str, Tuple[float, int, int, float]]):
        self.name: str = name
        self.medianPackageSize: Dict[str, Dict[str, float]] = medianPackageSize
        self.medianDelay: Dict[str, Dict[str, float]] = medianDelay
        self.medianProcessTime: Dict[str, Tuple[float, int, int, float]] = medianProcessTime
        tasksAndApps = loadDependencies()
        self.tasks: Dict[str, Task] = tasksAndApps[0]
        self.applications: Dict[str, Application] = tasksAndApps[1]

    def schedule(
            self,
            userName,
            userMachine,
            masterName,
            masterMachine,
            applicationName: str,
            label: str,
            availableWorkers: Dict[str, List[str]],
            workersResources: Dict[str, ResourcesInfo]
    ) -> Decision:
        edgesByName = self.__getExecutionMap(
            applicationName,
            label=label)
        return self._schedule(
            userName,
            userMachine,
            masterName,
            masterMachine,
            edgesByName,
            availableWorkers,
            workersResources)

    @abstractmethod
    def _schedule(
            self,
            userName,
            userMachine,
            masterName,
            masterMachine,
            edgesByName: EdgesByName,
            availableWorkers: Dict[str, List[str]],
            workersResources: Dict[str, ResourcesInfo]) -> Decision:
        raise NotImplementedError

    def __getExecutionMap(
            self,
            applicationName: str,
            label: str) -> EdgesByName:
        app = self.applications[applicationName]

        skipRoles = {'RemoteLogger'}
        replaceRoles = {'Sensor', 'Actor'}
        edgesByName = defaultdict(lambda: set([]))
        for taskName, dependency in app.dependencies.items():
            if taskName in skipRoles:
                continue
            if taskName in replaceRoles:
                taskName = 'Master-0'
            else:
                taskName = '%s@%s@TaskHandler' % (taskName, label)

            childTaskList = deepcopy(dependency.childTaskList)
            if 'Sensor' in childTaskList and 'Master' not in childTaskList:
                childTaskList.remove('Sensor')
                childTaskList.append('Master-0')
            if 'Actor' in childTaskList and 'Master' not in childTaskList:
                childTaskList.remove('Actor')
                childTaskList.append('Master-0')
            if 'RemoteLogger' in childTaskList:
                childTaskList.remove('RemoteLogger')
            for i, name in enumerate(childTaskList):
                if not name == 'Master-0':
                    childTaskList[i] = '%s@%s@TaskHandler' % (childTaskList[i], label)
                elif name == 'User':
                    childTaskList[i] = '%s@%s' % (applicationName, name)
            edgesByName[taskName].update(set(childTaskList))
        userAppName = '%s@%s@User' % (applicationName, label)
        edgesByName['Master-0'].update({userAppName})
        edgesByName[userAppName] = {'Master-0'}

        res = defaultdict(lambda: set([]))
        result = {}
        for k, v in edgesByName.items():
            for name in v:
                res[k].update([name])
            result[k] = list(res[k])
        return result


class Evaluator:

    def __init__(
            self,
            userName,
            userMachine,
            masterName,
            masterMachine,
            medianPackageSize: Dict[str, Dict[str, float]],
            medianDelay: Dict[str, Dict[str, float]],
            medianProcessTime: Dict[str, Tuple[float, int, int, float]],
            edgesByName: EdgesByName,
            workersResources: Dict[str, ResourcesInfo]):

        self.userName = userName
        self.userMachineID = userMachine
        self.masterName = masterName
        self.masterMachine = masterMachine
        self.medianPackageSize: Dict[str, Dict[str, float]] = medianPackageSize
        self.medianDelay: Dict[str, Dict[str, float]] = medianDelay
        self.medianProcessTime: Dict[str, Tuple[float, int, int, float]] = medianProcessTime
        self.edgesByName = edgesByName
        self.workersResources = workersResources

    def _edgePackageSize(self) -> float:
        packageSize = .0
        for source, destinations in self.edgesByName.items():
            if source not in self.medianPackageSize:
                packageSize += 4096 * len(destinations)
                continue
            for dest in destinations:
                if dest not in self.medianPackageSize[source]:
                    packageSize += 4096
                    continue
                packageSize += self.medianPackageSize[source][dest]
        # suppose bandwidth for all nodes are the same
        # and is 10 mb/ s
        # packageSize /= 10485
        return packageSize

    def _edgeDelay(self, individual: Dict[str, str]) -> float:
        delay = .0
        for source, destinations in self.edgesByName.items():
            sourceName = '%s#%s' % (source, individual[source])
            if sourceName not in self.medianDelay:
                delay += 0.01
                continue
            for dest in destinations:
                destName = '%s#%s' % (dest, individual[dest])
                if destName in self.medianDelay[sourceName]:
                    delay += self.medianDelay[sourceName][destName]
                    continue
                if individual[dest] in self.medianDelay[sourceName]:
                    delay += self.medianDelay[sourceName][individual[dest]]
                    continue
                delay += 0.01
        return delay

    def _computingCost(self, individual: Dict[str, str]) -> float:
        total = .0
        for machineName in self.edgesByName.keys():
            if not machineName[-11:] == 'TaskHandler':
                continue
            workerMachineId = individual[machineName]
            taskHandlerName = '%s#%s' % (machineName, workerMachineId)
            if taskHandlerName in self.medianProcessTime:
                total += self.considerRecentResources(taskHandlerName, workerMachineId)
                continue
            if workerMachineId in self.medianProcessTime:
                total += self.considerRecentResources(workerMachineId, workerMachineId)
                continue
            total += self.considerRecentResources(None, workerMachineId)
        return total

    def considerRecentResources(self, index, workerMachineId):
        resources = self.workersResources[workerMachineId]
        if index is None:
            availableMemFactor = 0.5 * resources.availableMemory
            availableCPUFactor = 0.5 * resources.currentCPUFrequency * (1 - resources.currentTotalCPUUsage)
            processTime = 1 / (availableCPUFactor + availableMemFactor)
            return processTime

        record = self.medianProcessTime[index]

        resourceMemPercent = resources.availableMemory / resources.totalMemory

        processTime = record[0]
        availableMemory = record[1]
        totalMemory = record[2]
        totalCPUUsage = record[3]
        recordCPUFrequency = record[4]

        recordMemPerCent = availableMemory / totalMemory

        factor = 0.5 * availableMemory / resources.availableMemory
        factor += 0.5 * recordCPUFrequency / resources.currentCPUFrequency
        factor *= resourceMemPercent / recordMemPerCent
        factor *= resources.currentTotalCPUUsage / totalCPUUsage
        processTime = processTime * factor

        return processTime


class BaseProblem(Problem, Evaluator):

    def __init__(
            self,
            userName,
            userMachine,
            masterName,
            masterMachine,
            medianPackageSize: Dict[str, Dict[str, float]],
            medianDelay: Dict[str, Dict[str, float]],
            medianProcessTime: Dict[str, Tuple[float, int, int, float]],
            edgesByName: EdgesByName,
            availableWorkers: Dict[str, set[str]],
            workersResources: Dict[str, ResourcesInfo]):
        self.medianPackageSize: Dict[str, Dict[str, float]] = medianPackageSize
        self.medianDelay: Dict[str, Dict[str, float]] = medianDelay
        Evaluator.__init__(
            self,
            userName,
            userMachine,
            masterName,
            masterMachine,
            medianPackageSize=self.medianPackageSize,
            medianDelay=self.medianDelay,
            medianProcessTime=medianProcessTime,
            edgesByName=edgesByName,
            workersResources=workersResources)
        self.variableNumber = len(edgesByName)
        self.availableWorkers = defaultdict(lambda: [])
        choicesEachVariable = [0 for _ in range(len(edgesByName.keys()))]
        for i, name in enumerate(edgesByName.keys()):
            if len(name) > len('TaskHandler') \
                    and name[-11:] == 'TaskHandler':
                # TODO: Change when support multiple masters
                taskName = name[:name.find('@')]
                for workerMachine, images in availableWorkers.items():
                    if taskName in images:
                        self.availableWorkers[name].append(workerMachine)
                        choicesEachVariable[i] += 1
                shuffle(self.availableWorkers[name])
                continue
            choicesEachVariable[i] = 1

        lowerBound = [0 for _ in range(self.variableNumber)]
        upperBound = choicesEachVariable
        Problem.__init__(
            self,
            xl=lowerBound,
            xu=upperBound,
            n_obj=4,
            n_var=self.variableNumber,
            type_var=np.int,
            elementwise_evaluation=True)

    def _evaluate(self, x, out, *args, **kwargs):
        x = x.astype(int)
        individual = self.indexesToMachines(x)

        # TODO: bandwidth
        # edgePackageSize = self._edgePackageSize()
        edgeDelay = self._edgeDelay(individual)
        computingCost = self._computingCost(individual)
        varReciprocal = self.considerVariance(x)
        # print(x, 0, edgeDelay, computingCost)
        out['F'] = anp.column_stack([0, edgeDelay, computingCost, varReciprocal])

    @staticmethod
    def considerVariance(indexes: List[int]):
        return 1 / np.var(indexes)

    def indexesToMachines(self, indexes: List[int]):
        res = {}
        keys = list(self.edgesByName.keys())
        for keysIndex, index in enumerate(indexes):
            key = keys[keysIndex]
            if len(key) <= len('TaskHandler'):
                continue
            if key[-11:] != 'TaskHandler':
                continue
            res[key] = self.availableWorkers[key][index]
        res[self.masterName] = self.masterMachine
        res[self.userName] = self.userMachineID
        return res


class NSGABase(Scheduler):
    def __init__(
            self,
            name: str,
            algorithm: GeneticAlgorithm,
            medianPackageSize: Dict[str, Dict[str, float]],
            medianDelay: Dict[str, Dict[str, float]],
            medianProcessTime: Dict[str, Tuple[float, int, int, float]],
            generationNum: int,
    ):
        self.__generationNum: int = generationNum
        super().__init__(
            name=name,
            medianPackageSize=medianPackageSize,
            medianDelay=medianDelay,
            medianProcessTime=medianProcessTime)
        self.__algorithm = algorithm

    def _schedule(
            self,
            userName,
            userMachine,
            masterName,
            masterMachine,
            edgesByName: EdgesByName,
            availableWorkers: Dict[str, set[str]],
            workersResources: Dict[str, ResourcesInfo]) -> Decision:
        problem = BaseProblem(
            userName,
            userMachine,
            masterName,
            masterMachine,
            medianPackageSize=self.medianPackageSize,
            medianDelay=self.medianDelay,
            medianProcessTime=self.medianProcessTime,
            edgesByName=edgesByName,
            availableWorkers=availableWorkers,
            workersResources=workersResources)
        res = minimize(problem,
                       self.__algorithm,
                       seed=randint(0, 100),
                       termination=(
                           'n_gen',
                           self.__generationNum))
        machines = problem.indexesToMachines(list(res.X[0].astype(int)))
        edgePackageSize = res.F[0][0]
        edgeDelay = res.F[0][1]
        computingCost = res.F[0][2]
        varReciprocal = res.F[0][3]
        decision = Decision(
            machines=machines,
            edgePackageSize=edgePackageSize,
            edgeDelay=edgeDelay,
            computingCost=computingCost,
            varReciprocal=varReciprocal)
        return decision


class NSGA2(NSGABase):

    def __init__(self,
                 populationSize: int,
                 generationNum: int,
                 medianPackageSize: Dict[str, Dict[str, float]],
                 medianDelay: Dict[str, Dict[str, float]],
                 medianProcessTime: Dict[str, Tuple[float, int, int, float]]):
        super().__init__(
            'NSGA2',
            NSGA2_(
                pop_size=populationSize,
                eliminate_duplicates=True),
            medianPackageSize=medianPackageSize,
            medianDelay=medianDelay,
            medianProcessTime=medianProcessTime,
            generationNum=generationNum)


class NSGA3(NSGABase):

    def __init__(self,
                 populationSize: int,
                 generationNum: int,
                 dasDennisP: int,
                 medianPackageSize: Dict[str, Dict[str, float]],
                 medianDelay: Dict[str, Dict[str, float]],
                 medianProcessTime: Dict[str, Tuple[float, int, int, float]]):
        refDirs = get_reference_directions(
            "das-dennis",
            4,
            n_partitions=dasDennisP)
        super().__init__(
            'NSGA3',
            NSGA3_(
                pop_size=populationSize,
                ref_dirs=refDirs,
                eliminate_duplicates=True),
            medianPackageSize=medianPackageSize,
            medianDelay=medianDelay,
            medianProcessTime=medianProcessTime,
            generationNum=generationNum)


class CTAEA(NSGABase):

    def __init__(self,
                 generationNum: int,
                 dasDennisP: int,
                 medianPackageSize: Dict[str, Dict[str, float]],
                 medianDelay: Dict[str, Dict[str, float]],
                 medianProcessTime: Dict[str, Tuple[float, int, int, float]]):
        refDirs = get_reference_directions(
            "das-dennis",
            4,
            n_partitions=dasDennisP)
        super().__init__(
            'CTAEA',
            CTAEA_(
                ref_dirs=refDirs,
                seed=randint(0, 100)),
            medianPackageSize=medianPackageSize,
            medianDelay=medianDelay,
            medianProcessTime=medianProcessTime,
            generationNum=generationNum)


if __name__ == '__main__':
    pass
