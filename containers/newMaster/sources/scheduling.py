import numpy as np
import threading
import json
import os
from queue import Queue
from random import randint, shuffle
from pymoo.algorithms.genetic_algorithm import GeneticAlgorithm
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
from datatype import Worker

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
            medianDelay: Dict[str, Dict[str, float]],
            medianProcessTime: Dict[str, Tuple[float, int, float]]):
        self.name: str = name
        self.medianDelay: Dict[str, Dict[str, float]] = medianDelay
        self.medianProcessTime: Dict[str, Tuple[float, int, float]] = medianProcessTime
        tasksAndApps = loadDependencies()
        self.tasks: Dict[str, Task] = tasksAndApps[0]
        self.applications: Dict[str, Application] = tasksAndApps[1]
        self.edgesByName = {}

    def schedule(
            self,
            userName,
            userMachine,
            masterName,
            masterMachine,
            applicationName: str,
            label: str,
            availableWorkers: Dict[str, Worker]
    ) -> Decision:
        edgesByName, entrance = self._getExecutionMap(
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
            availableWorkers: Dict[str, Worker]) -> Decision:
        raise NotImplementedError

    def _getExecutionMap(
            self,
            applicationName: str,
            label: str) -> Tuple[EdgesByName, str]:
        if applicationName in self.edgesByName:
            return self.edgesByName[applicationName]
        app = self.applications[applicationName]

        skipRoles = {'RemoteLogger'}
        replaceRoles = {'Sensor', 'Actor'}
        edgesByName = defaultdict(lambda: set([]))
        for taskName, dependency in app.dependencies.items():
            if taskName in skipRoles:
                continue
            if taskName in replaceRoles:
                taskName = 'Master'
            else:
                taskName = '%s@%s@TaskHandler' % (taskName, label)

            childTaskList = deepcopy(dependency.childTaskList)
            if 'Sensor' in childTaskList and 'Master' not in childTaskList:
                childTaskList.remove('Sensor')
                childTaskList.append('Master')
            if 'Actor' in childTaskList and 'Master' not in childTaskList:
                childTaskList.remove('Actor')
                childTaskList.append('Master')
            if 'RemoteLogger' in childTaskList:
                childTaskList.remove('RemoteLogger')
            for i, name in enumerate(childTaskList):
                if not name == 'Master':
                    childTaskList[i] = '%s@%s@TaskHandler' % (childTaskList[i], label)
                elif name == 'User':
                    childTaskList[i] = '%s@%s' % (applicationName, name)
            edgesByName[taskName].update(set(childTaskList))
        userAppName = '%s@%s@User' % (applicationName, label)
        edgesByName['Master'].update({userAppName})
        edgesByName[userAppName] = {'Master'}

        res = defaultdict(lambda: set([]))
        result = {}
        for k, v in edgesByName.items():
            for name in v:
                res[k].update([name])
            result[k] = list(res[k])
        self.edgesByName[applicationName] = result, userAppName
        return result, userAppName


class Evaluator:

    def __init__(
            self,
            userName,
            userMachine,
            masterName,
            masterMachine,
            medianDelay: Dict[str, Dict[str, float]],
            medianProcessTime: Dict[str, Tuple[float, int, float]],
            edgesByName: EdgesByName,
            entrance: str,
            workers: Dict[str, Worker]):
        self.userName = userName
        self._userMachineID = userMachine
        self.masterName = masterName
        self._masterMachine = masterMachine
        self.medianDelay: Dict[str, Dict[str, float]] = medianDelay
        self.medianProcessTime = medianProcessTime
        self._edgesByName = edgesByName
        self.entrance = entrance
        self.individual = None
        self.workers = workers

    def _cost(self, individual):
        self.individual = individual
        res = set([])
        master = 'Master'
        cost = self._edgeCost(self.entrance, master)
        cost += self._edgeCost(master, self.entrance)
        for dest in self._edgesByName[master]:
            self._dfs(
                dest,
                cost + self._edgeCost(master, dest),
                res)
        return max(res)

    def _dfs(self, source: str, cost: float, res: set):
        if source == 'Master':
            res.add(cost)
            return
        if source[-11:] == 'TaskHandler':
            cost += self._computingCost(source)
        for dest in self._edgesByName[source]:
            cost += self._edgeCost(source, dest)
            self._dfs(dest, cost, res)

    def _edgeCost(self, source, dest) -> float:
        sourceMachine = self.individual[source]
        sourceName = '%s#%s' % (source, sourceMachine)
        destMachine = self.individual[dest]
        destName = '%s#%s' % (dest, destMachine)
        if sourceName in self.medianDelay \
                and destName in self.medianDelay[sourceName]:
            return self.medianDelay[sourceName][destName]
        if sourceMachine not in self.medianDelay:
            return 1
        if destMachine not in self.medianDelay[sourceMachine]:
            return 1
        return self.medianDelay[sourceMachine][destMachine]

    def _computingCost(self, machineName) -> float:
        workerMachineId = self.individual[machineName]
        taskHandlerNameConsistent = '%s#%s' % (machineName, workerMachineId)
        if taskHandlerNameConsistent in self.medianProcessTime \
                and self.medianProcessTime[taskHandlerNameConsistent][0] != 0:
            return self.medianProcessTime[taskHandlerNameConsistent][0]
        if workerMachineId in self.medianProcessTime \
                and self.medianProcessTime[workerMachineId][0] != 0:
            return self.medianProcessTime[workerMachineId][0]
        return self.estimateComputingCost(machineName, workerMachineId)

    def estimateComputingCost(self, machineName, workerMachineId):
        worker = self.workers[workerMachineId]
        if machineName in self.medianProcessTime \
                and self.medianProcessTime[machineName][0] != 0:
            processTime = self.medianProcessTime[machineName][0]
            totalCPUCores = self.medianProcessTime[machineName][1]
            cpuFreq = self.medianProcessTime[machineName][2]
            processTime *= totalCPUCores * cpuFreq
            processTime /= worker.totalCPUCores * worker.cpuFreq
            return processTime
        return 1 / (worker.cpuFreq * worker.totalCPUCores)


class GeneticProblem(Problem, Evaluator):

    def __init__(
            self,
            userName,
            userMachine,
            masterName,
            masterMachine,
            medianDelay: Dict[str, Dict[str, float]],
            medianProcessTime: Dict[str, Tuple[float, int, float]],
            edgesByName: EdgesByName,
            entrance: str,
            availableWorkers: Dict[str, Worker],
            populationSize: int):
        self.populationSize = populationSize
        self.medianDelay: Dict[str, Dict[str, float]] = medianDelay
        Evaluator.__init__(
            self,
            userName,
            userMachine,
            masterName,
            masterMachine,
            medianDelay=self.medianDelay,
            medianProcessTime=medianProcessTime,
            edgesByName=edgesByName,
            entrance=entrance,
            workers=availableWorkers)
        self._variableNumber = len(edgesByName)
        self._availableWorkers = defaultdict(lambda: [])
        choicesEachVariable = [0 for _ in range(len(edgesByName.keys()))]
        for i, name in enumerate(edgesByName.keys()):
            if len(name) > len('TaskHandler') \
                    and name[-11:] == 'TaskHandler':
                # TODO: Change when support multiple masters
                taskName = name[:name.find('@')]
                for machineID, worker in availableWorkers.items():
                    # Tru for saving experiment time
                    if taskName in worker.images or True:
                        self._availableWorkers[name].append(worker.machineID)
                        choicesEachVariable[i] += 1
                shuffle(self._availableWorkers[name])
                continue
            choicesEachVariable[i] = 1

        lowerBound = [0 for _ in range(self._variableNumber)]
        upperBound = choicesEachVariable
        Problem.__init__(
            self,
            xl=lowerBound,
            xu=upperBound,
            n_obj=1,
            n_var=self._variableNumber,
            type_var=np.int)

        res = [.0 for _ in range(self.populationSize)]
        self._res = np.asarray(res)
        self._individualToProcess = Queue()
        self._runEvaluationThreadPool()
        self.myRecords = []

    def _runEvaluationThreadPool(self):
        for i in range(self.populationSize // 2):
            threading.Thread(
                target=self._evaluationThread
            ).start()

    def _evaluationThread(self):
        while True:
            i, individual, event = self._individualToProcess.get()
            self._res[i] = self._cost(individual)
            event.set()

    def _evaluate(self, xs, out, *args, **kwargs):

        events = [threading.Event() for _ in range(len(xs))]
        for i, x in enumerate(xs):
            x = x.astype(int)
            individual = self.indexesToMachines(x)
            self._individualToProcess.put((i, individual, events[i]))
        for event in events:
            event.wait()
        out['F'] = self._res
        self.myRecords.append(min(out['F']))

    def indexesToMachines(self, indexes: List[int]):
        res = {}
        keys = list(self._edgesByName.keys())
        for keysIndex, index in enumerate(indexes):
            key = keys[keysIndex]
            if len(key) <= len('TaskHandler'):
                continue
            if key[-11:] != 'TaskHandler':
                continue
            res[key] = self._availableWorkers[key][index]
        res[self.masterName] = self._masterMachine
        res[self.userName] = self._userMachineID
        return res


class NSGABase(Scheduler):
    def __init__(
            self,
            name: str,
            geneticAlgorithm: GeneticAlgorithm,
            medianDelay: Dict[str, Dict[str, float]],
            medianProcessTime: Dict[str, Tuple[float, int, float]],
            generationNum: int,
            populationSize: int
    ):
        self._generationNum: int = generationNum
        self._populationSize: int = populationSize
        self._geneticAlgorithm = geneticAlgorithm
        super().__init__(
            name=name,
            medianDelay=medianDelay,
            medianProcessTime=medianProcessTime)

    def _schedule(
            self,
            userName,
            userMachine,
            masterName,
            masterMachine,
            edgesByName: EdgesByName,
            entrance: str,
            availableWorkers: Dict[str, Worker]) -> Decision:
        geneticProblem = GeneticProblem(
            userName,
            userMachine,
            masterName,
            masterMachine,
            medianDelay=self.medianDelay,
            medianProcessTime=self.medianProcessTime,
            edgesByName=edgesByName,
            entrance=entrance,
            availableWorkers=availableWorkers,
            populationSize=self._populationSize)
        res = minimize(geneticProblem,
                       self._geneticAlgorithm,
                       seed=randint(0, 100),
                       termination=(
                           'n_gen',
                           self._generationNum))
        if len(res.X.shape) > 1:
            minIndex = np.argmin(res.F)
            cost = res.F[minIndex][0]
            indexes = res.X[minIndex]
            indexes = list(indexes.astype(int))
        else:
            cost = res.F[0]
            indexes = list(res.X.astype(int))
        machines = geneticProblem.indexesToMachines(indexes)
        self.saveEstimatingProgress(geneticProblem.myRecords)
        decision = Decision(
            machines=machines,
            cost=cost)
        return decision

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


def _initialize(self):
    # create the initial population
    pop = self.initialization.do(self.problem, self.pop_size, algorithm=self)
    print(pop[0].X, pop[0].F)
    pop.set("n_gen", self.n_gen)
    # then evaluate using the objective function
    self.evaluator.eval(self.problem, pop, algorithm=self)

    # that call is a dummy survival to set attributes that are necessary for the mating selection
    if self.survival:
        pop = self.survival.do(self.problem, pop, len(pop), algorithm=self,
                               n_min_infeas_survive=self.min_infeas_pop_size)

    self.pop, self.off = pop, pop


class NSGA2InitialWithLog(NSGA2_):

    def _initialize(self):
        return _initialize(self)


class NSGA2(NSGABase):

    def __init__(self,
                 populationSize: int,
                 generationNum: int,
                 medianDelay: Dict[str, Dict[str, float]],
                 medianProcessTime: Dict[str, Tuple[float, int, float]],
                 initWithLog: bool = False):

        if not initWithLog:
            algorithm = NSGA2_(
                pop_size=populationSize,
                eliminate_duplicates=True)
        else:
            algorithm = NSGA2InitialWithLog(
                pop_size=populationSize,
                eliminate_duplicates=True)
        super().__init__(
            'NSGA2',
            algorithm,
            medianDelay=medianDelay,
            medianProcessTime=medianProcessTime,
            generationNum=generationNum,
            populationSize=populationSize)


class NSGA3InitialWithLog(NSGA3_):

    def _initialize(self):
        return _initialize(self)


class NSGA3(NSGABase):

    def __init__(self,
                 populationSize: int,
                 generationNum: int,
                 dasDennisP: int,
                 medianDelay: Dict[str, Dict[str, float]],
                 medianProcessTime: Dict[str, Tuple[float, int, float]],
                 initWithLog: bool = False):
        refDirs = get_reference_directions(
            "das-dennis",
            1,
            n_partitions=dasDennisP)
        if not initWithLog:
            algorithm = NSGA3_(
                pop_size=populationSize,
                ref_dirs=refDirs,
                eliminate_duplicates=True)
        else:
            algorithm = NSGA3InitialWithLog(
                pop_size=populationSize,
                ref_dirs=refDirs,
                eliminate_duplicates=True)
        super().__init__(
            'NSGA3',
            algorithm,
            medianDelay=medianDelay,
            medianProcessTime=medianProcessTime,
            generationNum=generationNum,
            populationSize=populationSize)


if __name__ == '__main__':
    pass
