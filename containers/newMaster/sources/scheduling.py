import numpy as np
import threading
import json
import os
from queue import Queue
from random import randint, shuffle
from pymoo.algorithms.genetic_algorithm import GeneticAlgorithm
from pymoo.factory import get_crossover, get_mutation, get_sampling
from pymoo.algorithms.nsga3 import NSGA3 as NSGA3_
from pymoo.algorithms.nsga2 import NSGA2 as NSGA2_
from pymoo.factory import get_reference_directions
from pymoo.optimize import minimize
from pymoo.operators.selection.tournament_selection import TournamentSelection, compare
from abc import abstractmethod
from pymoo.model.problem import Problem
from pymoo.model.population import Population
from pymoo.model.evaluator import Evaluator as Evaluator_
from typing import Dict, List, Tuple, Union
from dependencies import loadDependencies, Task, Application
from copy import deepcopy
from collections import defaultdict
from pprint import pformat
from pymoo.configuration import Configuration
from hashlib import sha256
from datatype import Worker
import math
from pymoo.model.selection import Selection
from pymoo.util.misc import random_permuations

Configuration.show_compile_hint = False
EdgesByName = Dict[str, List[str]]


class MyTournamentSelection(Selection):
    """
      The Tournament selection is used to simulated a tournament between individuals. The pressure balances
      greedy the genetic algorithm will be.
    """

    def __init__(self, func_comp=None, pressure=2):
        """

        Parameters
        ----------
        func_comp: func
            The function to compare two individuals. It has the shape: comp(pop, indices) and returns the winner.
            If the function is None it is assumed the population is sorted by a criterium and only indices are compared.

        pressure: int
            The selection pressure to bie applied. Default it is a binary tournament.
        """

        # selection pressure to be applied
        super().__init__()
        self.pressure = pressure

        self.f_comp = func_comp
        if self.f_comp is None:
            raise Exception("Please provide the comparing function for the tournament selection!")

    def _do(self, pop, n_select, n_parents=1, **kwargs):
        # print('n_select: ', n_select)
        # number of random individuals needed
        n_random = n_select * n_parents * self.pressure

        # number of permutations needed
        n_perms = math.ceil(n_random / len(pop))

        # get random permutations and reshape them
        P = random_permuations(n_perms, len(pop))[:n_random]
        P = np.reshape(P, (n_select * n_parents, self.pressure))

        # compare using tournament function
        S = self.f_comp(pop, P, **kwargs)

        return np.reshape(S, (n_select, n_parents))


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
            cost: float,
            machinesIndex: List[int],
            indexToMachine: List[str]):
        self.machines: Dict[str, str] = machines
        self.cost: float = cost
        self.machinesIndex = machinesIndex
        self.indexToMachine = indexToMachine

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
            medianProcessTime: Dict[str, Tuple[float, int, float]],
            bps: Dict[str, Dict[str, float]],
            ping: Dict[str, Dict[str, float]],
            medianPackageSize: Dict[str, Dict[str, float]],
    ):
        self.name: str = name
        self.medianDelay: Dict[str, Dict[str, float]] = medianDelay
        self.medianProcessTime: Dict[str, Tuple[float, int, float]] = medianProcessTime
        tasksAndApps = loadDependencies()
        self.tasks: Dict[str, Task] = tasksAndApps[0]
        self.applications: Dict[str, Application] = tasksAndApps[1]
        self.edgesByName = {}
        self.bps = bps
        self.ping = ping
        self.medianPackageSize = medianPackageSize

    def schedule(
            self,
            userName,
            userMachine,
            masterName,
            masterMachine,
            applicationName: str,
            label: str,
            availableWorkers: Dict[str, Worker],
            machinesIndex) -> Decision:
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
            availableWorkers,
            machinesIndex)

    @abstractmethod
    def _schedule(
            self,
            userName,
            userMachine,
            masterName,
            masterMachine,
            edgesByName: EdgesByName,
            entrance: str,
            availableWorkers: Dict[str, Worker],
            machinesIndex) -> Decision:
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
        print(userAppName)
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
            bps: Dict[str, Dict[str, float]],
            ping: Dict[str, Dict[str, float]],
            medianPackageSize: Dict[str, Dict[str, float]],
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
        self.edgesByName = edgesByName
        self.bps = bps
        self.ping = ping
        self.medianPackageSize = medianPackageSize
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

        if sourceMachine == destMachine:
            return 0

        if sourceMachine in self.ping \
                and destMachine in self.ping[sourceMachine]:
            pingCost = self.ping[sourceMachine][destMachine]
            bps = self.bps[sourceMachine][destMachine]
            if sourceName in self.medianPackageSize \
                    and destName in self.medianPackageSize[sourceName]:
                packageSize = self.medianPackageSize[sourceName][destName]
                bytePerSecond = bps / 8
                return (packageSize / bytePerSecond * 1000) + pingCost
            return pingCost

        if sourceMachine in self.medianDelay \
                and destMachine in self.medianDelay[sourceMachine]:
            return self.medianDelay[sourceMachine][destMachine]
        return 1

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
        divider = worker.cpuFreq * worker.totalCPUCores
        if divider == 0:
            return 1
        return 1 / divider


class GeneticProblem(Problem, Evaluator):

    def __init__(
            self,
            userName,
            userMachine,
            masterName,
            masterMachine,
            medianDelay: Dict[str, Dict[str, float]],
            bps: Dict[str, Dict[str, float]],
            ping: Dict[str, Dict[str, float]],
            medianPackageSize: Dict[str, Dict[str, float]],
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
            bps=bps,
            ping=ping,
            medianPackageSize=medianPackageSize,
            medianProcessTime=medianProcessTime,
            edgesByName=edgesByName,
            entrance=entrance,
            workers=availableWorkers)

        self._variableNumber = len(edgesByName)
        self._availableWorkers = defaultdict(lambda: [])
        choicesEachVariable = [-1 for _ in range(len(edgesByName.keys()))]
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
                # I wrote this to remind me myself of
                # how stupid I am
                # shuffle(self._availableWorkers[name])
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
        # print('[Population]: ')
        events = [threading.Event() for _ in range(len(xs))]
        for i, x in enumerate(xs):
            # print('chromosome ----> ', x)
            individual = self.indexesToMachines(x)
            # print(individual)
            self._individualToProcess.put((i, individual, events[i]))
        for event in events:
            event.wait()
        out['F'] = self._res
        self.myRecords.append(min(out['F']))
        # print('< ---- ', min(out['F']))
        # print('=========================')

    def replaceX(self, xs, machinesIndex):
        machineToIndex = {}
        keys = list(self.edgesByName.keys())
        for i, machine in enumerate(keys):
            machineToIndex[machine] = i
        for i, (indexes, machines) in enumerate(machinesIndex):
            machineX = [machines[j] for j in indexes]
            x = [machineToIndex[machine] for machine in machineX]
            if x.count(x[0]) / len(x) > .8:
                maxIndex = max(x)
                for j in range(len(x)):
                    randNum = np.random.random(1)[0]
                    if randNum < .3:
                        x[j] = np.random.randint(maxIndex + 1)
                # print(x)
            # x = [0 for machine in machineX]
            xs[i] = x

        return xs

    def indexesToMachines(self, indexes: List[int]):
        res = {}
        keys = list(self.edgesByName.keys())
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
            bps: Dict[str, Dict[str, float]],
            ping: Dict[str, Dict[str, float]],
            medianPackageSize: Dict[str, Dict[str, float]],
            medianProcessTime: Dict[str, Tuple[float, int, float]],
            generationNum: int,
            populationSize: int
    ):
        self.generationNum: int = generationNum
        self.populationSize: int = populationSize
        self.geneticAlgorithm = geneticAlgorithm
        super().__init__(
            name=name,
            medianDelay=medianDelay,
            medianProcessTime=medianProcessTime,
            bps=bps,
            ping=ping,
            medianPackageSize=medianPackageSize
        )
        self.geneticProblem = None

    @staticmethod
    def selectionCmp(pop, P, **kwargs):
        # print('[P]: ', P)
        S = np.full(P.shape[0], np.nan)
        # print('[Selection]: ')
        for i in range(P.shape[0]):
            a, b = P[i, 0], P[i, 1]
            if pop[a].CV > 0.0 or pop[b].CV > 0.0:
                S[i] = compare(a, pop[a].CV, b, pop[b].CV, method='smaller_is_better', return_random_if_equal=True)
                # print('Used cv to select: -> ', S[i], pop[S[i]])
                # print(' -> ', pop[int(S[i])].X)
                continue
            if pop[a].F > 0.0 or pop[b].F > 0.0:
                S[i] = compare(a, pop[a].F, b, pop[b].F, method='smaller_is_better', return_random_if_equal=True)
                # print('Used F to select: -> ', S[i], pop[S[i]])
                # print(' -> ', pop[int(S[i])].X)
                continue
            # both solutions are feasible just set random
            S[i] = np.random.choice([a, b])
            # print(' -> ', pop[int(S[i])].X)

            # print('randomly selected: -> ', S[i], pop[S[i]])

        # print('%%%%%%%%%%%%%')

        return S[:, None].astype(np.int, copy=False)

    def _schedule(
            self,
            userName,
            userMachine,
            masterName,
            masterMachine,
            edgesByName: EdgesByName,
            entrance: str,
            availableWorkers: Dict[str, Worker],
            machinesIndex) -> Decision:

        self.geneticProblem = GeneticProblem(
            userName,
            userMachine,
            masterName,
            masterMachine,
            medianDelay=self.medianDelay,
            bps=self.bps,
            ping=self.ping,
            medianPackageSize=self.medianPackageSize,
            medianProcessTime=self.medianProcessTime,
            edgesByName=edgesByName,
            entrance=entrance,
            availableWorkers=availableWorkers,
            populationSize=self.populationSize)

        if len(machinesIndex):
            X = np.random.randint(
                low=0,
                high=max(machinesIndex[0][0]) + 1,
                size=(self.geneticProblem.populationSize,
                      self.geneticProblem.n_var))
            X = self.geneticProblem.replaceX(
                X,
                machinesIndex=machinesIndex)
            pop = Population.new("X", X)
            Evaluator_().eval(self.geneticProblem, pop)
            for i in range(len(pop)):
                # print(chromosome.CV, chromosome.F)
                pop[i].CV = pop[i].F
            # Evaluator().eval(self.geneticProblem, pop)
            crossover = get_crossover(
                "int_sbx",
                prob=0.5,
                eta=3.0)
            mutation = get_mutation("int_pm", eta=3.0)
            selection = MyTournamentSelection(
                func_comp=self.selectionCmp)
            if isinstance(self.geneticAlgorithm, NSGA2_):
                self.geneticAlgorithm = NSGA2_(
                    pop_size=self.geneticAlgorithm.pop_size,
                    sampling=pop,
                    crossover=crossover,
                    mutation=mutation,
                    selection=selection,
                    eliminate_duplicates=False)
            if isinstance(self.geneticAlgorithm, NSGA3_):
                self.geneticAlgorithm = NSGA3_(
                    pop_size=self.geneticAlgorithm.pop_size,
                    sampling=pop,
                    crossover=crossover,
                    mutation=mutation,
                    selection=selection,
                    ref_dirs=self.geneticAlgorithm.ref_dirs,
                    eliminate_duplicates=False)
            print('[*] Initialized with %d individuals' % len(machinesIndex))

        res = minimize(self.geneticProblem,
                       self.geneticAlgorithm,
                       seed=randint(0, 100),
                       termination=(
                           'n_gen',
                           self.generationNum))
        if len(res.X.shape) > 1:
            minIndex = np.argmin(res.F)
            cost = res.F[minIndex][0]
            indexes = res.X[minIndex]
            indexes = list(indexes.astype(int))
        else:
            cost = res.F[0]
            indexes = list(res.X.astype(int))
        machines = self.geneticProblem.indexesToMachines(indexes)
        self.saveEstimatingProgress(self.geneticProblem.myRecords)
        decision = Decision(
            machines=machines,
            cost=cost,
            machinesIndex=indexes,
            indexToMachine=list(self.geneticProblem.edgesByName.keys()))
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


class NSGA2(NSGABase):

    def __init__(self,
                 populationSize: int,
                 generationNum: int,
                 medianDelay: Dict[str, Dict[str, float]],
                 bps: Dict[str, Dict[str, float]],
                 ping: Dict[str, Dict[str, float]],
                 medianPackageSize: Dict[str, Dict[str, float]],
                 medianProcessTime: Dict[str, Tuple[float, int, float]],
                 sampling=get_sampling("int_random")):
        geneticAlgorithm = NSGA2_(
            pop_size=populationSize,
            sampling=sampling,
            crossover=get_crossover("int_sbx", prob=1.0, eta=3.0),
            mutation=get_mutation("int_pm", eta=3.0),
            eliminate_duplicates=False)
        super().__init__(
            'NSGA2',
            geneticAlgorithm,
            medianDelay=medianDelay,
            medianProcessTime=medianProcessTime,
            generationNum=generationNum,
            populationSize=populationSize,
            bps=bps,
            ping=ping,
            medianPackageSize=medianPackageSize
        )


class NSGA3(NSGABase):

    def __init__(self,
                 populationSize: int,
                 generationNum: int,
                 dasDennisP: int,
                 medianDelay: Dict[str, Dict[str, float]],
                 bps: Dict[str, Dict[str, float]],
                 ping: Dict[str, Dict[str, float]],
                 medianPackageSize: Dict[str, Dict[str, float]],
                 medianProcessTime: Dict[str, Tuple[float, int, float]],
                 sampling=get_sampling("int_random")):
        refDirs = get_reference_directions(
            "das-dennis",
            1,
            n_partitions=dasDennisP)
        algorithm = NSGA3_(
            pop_size=populationSize,
            sampling=sampling,
            crossover=get_crossover("int_sbx", prob=1.0, eta=3.0),
            mutation=get_mutation("int_pm", eta=3.0),
            ref_dirs=refDirs,
            eliminate_duplicates=False)
        super().__init__(
            'NSGA3',
            algorithm,
            medianDelay=medianDelay,
            medianProcessTime=medianProcessTime,
            generationNum=generationNum,
            populationSize=populationSize,
            bps=bps,
            ping=ping,
            medianPackageSize=medianPackageSize
        )


if __name__ == '__main__':
    pass
