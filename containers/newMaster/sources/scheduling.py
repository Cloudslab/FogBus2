import numpy as np
from pprint import pprint
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
            cost: float):
        self.machines: Dict[str, str] = machines
        self.cost: float = cost

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
            medianProcessTime: Dict[str, Tuple[float, int, int, float, float]]):
        self.name: str = name
        self.medianPackageSize: Dict[str, Dict[str, float]] = medianPackageSize
        self.medianDelay: Dict[str, Dict[str, float]] = medianDelay
        self.medianProcessTime: Dict[str, Tuple[float, int, int, float, float]] = medianProcessTime
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
            availableWorkers: Dict[str, List[str]]
    ) -> Decision:
        edgesByName, entrance = self.__getExecutionMap(
            applicationName,
            label=label)
        return self._schedule(
            userName,
            userMachine,
            masterName,
            masterMachine,
            edgesByName,
            entrance,
            availableWorkers)

    @abstractmethod
    def _schedule(
            self,
            userName,
            userMachine,
            masterName,
            masterMachine,
            edgesByName: EdgesByName,
            entrance: str,
            availableWorkers: Dict[str, List[str]]) -> Decision:
        raise NotImplementedError

    def __getExecutionMap(
            self,
            applicationName: str,
            label: str) -> Tuple[EdgesByName, str]:
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
        return result, userAppName


class Evaluator:

    def __init__(
            self,
            userName,
            userMachine,
            masterName,
            masterMachine,
            medianPackageSize: Dict[str, Dict[str, float]],
            medianDelay: Dict[str, Dict[str, float]],
            medianProcessTime: Dict[str, Tuple[float, int, int, float, float]],
            edgesByName: EdgesByName,
            entrance: str):

        self.userName = userName
        self.userMachineID = userMachine
        self.masterName = masterName
        self.masterMachine = masterMachine
        self.medianPackageSize: Dict[str, Dict[str, float]] = medianPackageSize
        self.medianDelay: Dict[str, Dict[str, float]] = medianDelay
        self.medianProcessTime = medianProcessTime
        self.edgesByName = edgesByName
        self.entrance = entrance
        self.individual = None

    def _cost(self, individual):
        self.individual = individual
        res = set([])
        master = 'Master-0'
        cost = self._edgeCost(self.entrance, master)
        cost += self._edgeCost(master, self.entrance)
        for dest in self.edgesByName[master]:
            self._dfs(
                dest,
                cost + self._edgeCost(master, dest),
                res)
        return max(res)

    def _dfs(self, source: str, cost: float, res: set):
        if source == 'Master-0':
            res.add(cost)
            return
        if source[-11:] == 'TaskHandler':
            cost += self._computingCost(source)
        for dest in self.edgesByName[source]:
            cost += self._edgeCost(source, dest)
            self._dfs(dest, cost, res)

    def _edgeCost(self, source, dest) -> float:
        sourceName = '%s#%s' % (source, self.individual[source])
        if sourceName not in self.medianDelay:
            return 1
        destName = '%s#%s' % (dest, self.individual[dest])
        if destName not in self.medianDelay[sourceName]:
            return 1
        return self.medianDelay[sourceName][destName]

    def _computingCost(self, machineName) -> float:
        workerMachineId = self.individual[machineName]
        taskHandlerName = '%s#%s' % (machineName, workerMachineId)
        if taskHandlerName in self.medianProcessTime:
            return self.considerRecentResources(taskHandlerName, workerMachineId)
        if workerMachineId in self.medianProcessTime:
            return self.considerRecentResources(workerMachineId, workerMachineId)
        return self.evaluateComputingCost()

    def evaluateComputingCost(self):
        return 1

    def considerRecentResources(self, index, workerMachineId):
        record = self.medianProcessTime[index]
        processTime = record
        return 1


class BaseProblem(Problem, Evaluator):

    def __init__(
            self,
            userName,
            userMachine,
            masterName,
            masterMachine,
            medianPackageSize: Dict[str, Dict[str, float]],
            medianDelay: Dict[str, Dict[str, float]],
            medianProcessTime: Dict[str, Tuple[float, int, int, float, float]],
            edgesByName: EdgesByName,
            entrance: str,
            availableWorkers: Dict[str, set[str]]):
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
            entrance=entrance)
        pprint(edgesByName)
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
            n_obj=1,
            n_var=self.variableNumber,
            type_var=np.int,
            elementwise_evaluation=True)

    def _evaluate(self, x, out, *args, **kwargs):
        x = x.astype(int)
        individual = self.indexesToMachines(x)
        out['F'] = self._cost(individual)

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
            medianProcessTime: Dict[str, Tuple[float, int, int, float, float]],
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
            entrance: str,
            availableWorkers: Dict[str, set[str]]) -> Decision:
        problem = BaseProblem(
            userName,
            userMachine,
            masterName,
            masterMachine,
            medianPackageSize=self.medianPackageSize,
            medianDelay=self.medianDelay,
            medianProcessTime=self.medianProcessTime,
            edgesByName=edgesByName,
            entrance=entrance,
            availableWorkers=availableWorkers)
        res = minimize(problem,
                       self.__algorithm,
                       seed=randint(0, 100),
                       termination=(
                           'n_gen',
                           self.__generationNum))
        machines = problem.indexesToMachines(list(res.X.astype(int)))
        cost = res.F[0]
        decision = Decision(
            machines=machines,
            cost=cost)
        return decision


class NSGA2(NSGABase):

    def __init__(self,
                 populationSize: int,
                 generationNum: int,
                 medianPackageSize: Dict[str, Dict[str, float]],
                 medianDelay: Dict[str, Dict[str, float]],
                 medianProcessTime: Dict[str, Tuple[float, int, int, float, float]]):
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
                 medianProcessTime: Dict[str, Tuple[float, int, int, float, float]]):
        refDirs = get_reference_directions(
            "das-dennis",
            1,
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
                 medianProcessTime: Dict[str, Tuple[float, int, int, float, float]]):
        refDirs = get_reference_directions(
            "das-dennis",
            1,
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
