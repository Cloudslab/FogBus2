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
            availableWorkers: Dict[str, Worker]) -> Decision:
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
        self.userMachineID = userMachine
        self.masterName = masterName
        self.masterMachine = masterMachine
        self.medianDelay: Dict[str, Dict[str, float]] = medianDelay
        self.medianProcessTime = medianProcessTime
        self.edgesByName = edgesByName
        self.entrance = entrance
        self.individual = None
        self.workers = workers

    def _cost(self, individual):
        self.individual = individual
        res = set([])
        master = 'Master'
        cost = self._edgeCost(self.entrance, master)
        cost += self._edgeCost(master, self.entrance)
        for dest in self.edgesByName[master]:
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
        for dest in self.edgesByName[source]:
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
        return self.evaluateComputingCost(machineName, workerMachineId)

    def evaluateComputingCost(self, machineName, workerMachineId):
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


class BaseProblem(Problem, Evaluator):

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
        self.variableNumber = len(edgesByName)
        self.availableWorkers = defaultdict(lambda: [])
        choicesEachVariable = [0 for _ in range(len(edgesByName.keys()))]
        for i, name in enumerate(edgesByName.keys()):
            if len(name) > len('TaskHandler') \
                    and name[-11:] == 'TaskHandler':
                # TODO: Change when support multiple masters
                taskName = name[:name.find('@')]
                for machineID, worker in availableWorkers.items():
                    # Tru for saving experiment time
                    if taskName in worker.images or True:
                        self.availableWorkers[name].append(worker.machineID)
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
            type_var=np.int)

        res = [.0 for _ in range(self.populationSize)]
        self.res = np.asarray(res)
        self.toProcess = Queue()
        self._runEvaluateThreadPool()
        self.record = []

    def _runEvaluateThreadPool(self):
        for i in range(self.populationSize // 2):
            threading.Thread(
                target=self._evaluateThread
            ).start()

    def _evaluateThread(self):
        while True:
            i, individual, event = self.toProcess.get()
            self.res[i] = self._cost(individual)
            event.set()

    def _evaluate(self, xs, out, *args, **kwargs):
        events = [threading.Event() for _ in range(len(xs))]
        for i, x in enumerate(xs):
            x = x.astype(int)
            individual = self.indexesToMachines(x)
            self.toProcess.put((i, individual, events[i]))
        for event in events:
            event.wait()
        out['F'] = self.res
        self.record.append(min(out['F']))

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
            medianDelay: Dict[str, Dict[str, float]],
            medianProcessTime: Dict[str, Tuple[float, int, float]],
            generationNum: int,
            populationSize: int
    ):
        self.__generationNum: int = generationNum
        self.__populationSize: int = populationSize
        super().__init__(
            name=name,
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
            availableWorkers: Dict[str, Worker]) -> Decision:
        problem = BaseProblem(
            userName,
            userMachine,
            masterName,
            masterMachine,
            medianDelay=self.medianDelay,
            medianProcessTime=self.medianProcessTime,
            edgesByName=edgesByName,
            entrance=entrance,
            availableWorkers=availableWorkers,
            populationSize=self.__populationSize)
        res = minimize(problem,
                       self.__algorithm,
                       seed=randint(0, 100),
                       termination=(
                           'n_gen',
                           self.__generationNum))
        machines = problem.indexesToMachines(list(res.X.astype(int)))
        cost = res.F[0]
        self.saveEvaluateProgress(problem.record)
        decision = Decision(
            machines=machines,
            cost=cost)
        return decision

    @staticmethod
    def saveEvaluateProgress(record):
        filename = './record.json'
        with open(filename, 'w+') as f:
            json.dump(record, f)
            f.close()
            try:
                os.chmod(filename, 0o666)
            except PermissionError:
                pass


class NSGA2(NSGABase):

    def __init__(self,
                 populationSize: int,
                 generationNum: int,
                 medianDelay: Dict[str, Dict[str, float]],
                 medianProcessTime: Dict[str, Tuple[float, int, float]]):
        super().__init__(
            'NSGA2',
            NSGA2_(
                pop_size=populationSize,
                eliminate_duplicates=True),
            medianDelay=medianDelay,
            medianProcessTime=medianProcessTime,
            generationNum=generationNum,
            populationSize=populationSize)


class NSGA3(NSGABase):

    def __init__(self,
                 populationSize: int,
                 generationNum: int,
                 dasDennisP: int,
                 medianDelay: Dict[str, Dict[str, float]],
                 medianProcessTime: Dict[str, Tuple[float, int, float]]):
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
            medianDelay=medianDelay,
            medianProcessTime=medianProcessTime,
            generationNum=generationNum,
            populationSize=populationSize)


if __name__ == '__main__':
    pass
