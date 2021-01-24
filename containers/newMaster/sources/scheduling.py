import numpy as np
import autograd.numpy as anp

from time import time
from random import randint
from profilerManage import Profiler
from pymoo.algorithms.nsga3 import NSGA3 as NSGA3_
from pymoo.factory import get_reference_directions
from pymoo.optimize import minimize
from persistentStorage import PersistentStorage
from abc import abstractmethod
from pymoo.model.problem import Problem
from typing import Dict, DefaultDict, List
from edge import Edge
from dependencies import loadDependencies, Task, Application
from copy import deepcopy
from collections import defaultdict
from pprint import pformat

EdgesByName = DefaultDict[str, List[str]]
MachinesByName = DefaultDict[str, List[str]]


class Decision:

    def __init__(
            self,
            machines: Dict[str, str],
            edgeCost: float,
            computingCost: float,
    ):
        self.machines: Dict[str, str] = machines
        self.edgeCost: float = edgeCost
        self.computingCost: float = computingCost

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return pformat(
            object=self.__dict__,
            indent=3)


class SchedulingMethod:

    def __init__(
            self,
            edges: Dict[str, Edge],
            averageProcessTime: Dict[str, float]):
        self.edges: Dict[str, Edge] = edges
        self.averageProcessTime: Dict[str, float] = averageProcessTime
        tasksAndApps = loadDependencies()
        self.tasks: Dict[str, Task] = tasksAndApps[0]
        self.applications: Dict[str, Application] = tasksAndApps[1]

    def schedule(
            self,
            applicationName: str,
            label: str,
            userMachineID: str) -> Decision:
        edgesByName = self.__getExecutionMap(
            applicationName,
            label=label)
        machinesByName = self.__getMachinesByName(
            applicationName=applicationName,
            label=label,
            userMachineID=userMachineID)
        return self.__schedule(edgesByName, machinesByName)

    @abstractmethod
    def __schedule(
            self,
            edgesByName: EdgesByName,
            machinesByName: MachinesByName) -> Decision:
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

        # lowercase all
        res = defaultdict(lambda: set([]))
        for k, v in edgesByName.items():
            for name in v:
                res[k].update([name])
            res[k] = list(res[k])
        return res

    def __getMachinesByName(
            self,
            applicationName: str,
            label: str,
            userMachineID: str) -> MachinesByName:
        userName = '%s@%s@User' % (applicationName, label)
        res = defaultdict(lambda: set([]))
        skipNames = {'RemoteLogger', 'Worker'}
        for edge in self.edges.values():
            source = edge.source.split('#')
            name = source[-2]
            if name in skipNames:
                continue
            machineID = source[-1]
            if name == userName:
                if not machineID == userMachineID:
                    continue
            res[name].update([machineID])
        for k, v in res.items():
            res[k] = list(v)
        return res


class NSGA3Problem(Problem):

    def __init__(
            self,
            edges: Dict[str, Edge],
            averageProcessTime: Dict[str, float],
            edgesByName: EdgesByName,
            machinesByName: MachinesByName):
        self.edges: Dict[str, Edge] = edges
        self.averageProcessTime: Dict[str, float] = averageProcessTime
        self.edgesByName = edgesByName
        self.machinesByName = machinesByName
        self.variableNumber = len(edgesByName)
        choicesEachVariable = [
            len(machinesByName[name]) for name in edgesByName.keys()]
        lowerBound = [0 for _ in range(self.variableNumber)]
        upperBound = choicesEachVariable
        super().__init__(
            xl=lowerBound,
            xu=upperBound,
            n_obj=2,
            n_var=self.variableNumber,
            type_var=np.int,
            elementwise_evaluation=True)

    def _evaluate(self, x, out, *args, **kwargs):
        x = x.astype(int)
        individual = self.indexesToNames(x)

        edgeCost = self.__edgeCost(individual)
        computingCost = self.__computingCost(individual)

        out['F'] = anp.column_stack([edgeCost, computingCost])

    def __edgeCost(self, individual: Dict[str, str]) -> float:
        total = .0
        for source, destinations in self.edgesByName.items():
            sourceName = '%s#%s' % (source, individual[source])
            for dest in destinations:
                destName = '%s#%s' % (dest, individual[dest])
                costKey = '%s,%s' % (sourceName, destName)
                total += self.edges[costKey].averageReceivedPackageSize
                total += self.edges[costKey].averageRoundTripDelay
        # suppose bandwidth for all nodes are the same
        # and is 0.1 mb/ ms
        return total / (1024 ** 2 / 10)

    def __computingCost(self, individual: Dict[str, str]) -> float:
        total = .0
        for machineName in self.edgesByName.keys():
            if not machineName.split('@')[-1] == 'TaskHandler':
                continue
            taskHandlerName = '%s#%s' % (machineName, individual[machineName])
            total += self.averageProcessTime[taskHandlerName]
        return total

    def indexesToNames(self, indexes: List[int]):
        res = {}
        keys = list(self.edgesByName.keys())
        for keysIndex, index in enumerate(indexes):
            key = keys[keysIndex]
            res[key] = self.machinesByName[key][index]
        return res


class NSGA3(SchedulingMethod):
    def __init__(
            self,
            edges: Dict[str, Edge],
            averageProcessTime: Dict[str, float],
            dasDennisP: int = 1,
            populationSize: int = 92,
            generationNum: int = 600,
    ):
        self.__generationNum: int = generationNum
        super().__init__(
            edges=edges,
            averageProcessTime=averageProcessTime)
        self.__refDirs = get_reference_directions(
            "das-dennis",
            2,
            n_partitions=dasDennisP)
        self.__algorithm = NSGA3_(
            pop_size=populationSize,
            ref_dirs=self.__refDirs,
            eliminate_duplicates=True)
        self._SchedulingMethod__schedule = self.__schedule

    def __schedule(
            self,
            edgesByName: EdgesByName,
            machinesByName: MachinesByName) -> Decision:
        problem = NSGA3Problem(
            edges=self.edges,
            averageProcessTime=self.averageProcessTime,
            edgesByName=edgesByName,
            machinesByName=machinesByName)
        res = minimize(problem,
                       self.__algorithm,
                       seed=randint(0, int(time() % 0.01 * 10000)),
                       termination=(
                           'n_gen',
                           self.__generationNum))
        machines = problem.indexesToNames(list(res.X[0].astype(int)))
        edgeCost = res.F[0][0]
        computingCost = res.F[0][1]
        decision = Decision(
            machines=machines,
            edgeCost=edgeCost,
            computingCost=computingCost)
        return decision


if __name__ == '__main__':
    profiler = Profiler()
    storage = PersistentStorage()
    schedulingMethod = NSGA3(
        edges=profiler.edges,
        averageProcessTime=profiler.averageProcessTime,
        generationNum=10)
    decision_ = schedulingMethod.schedule(
        applicationName='FaceAndEyeDetection',
        label='480',
        userMachineID='6fac209f965eb662d0465ce573322265ac07e12c3ca8b93f13bd0aaff2979b25')
    print(decision_)
