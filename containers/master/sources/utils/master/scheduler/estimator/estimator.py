from functools import lru_cache
from random import randint
from typing import Dict
from typing import List
from typing import Tuple
from typing import Union

from ...application.task.base import Task
from ...application.task.dependency.base import TaskWithDependency
from ...logger.allSystemPerformance import AllSystemPerformance
from ...registry.roles import Actor
from ...registry.roles import Master
from ...registry.roles import User
from ...registry.roles.nameFactory import NameFactory
from ....tools.camelToSnake import camelToSnake
from ....types import Component


class Estimator:

    def __init__(
            self,
            user: User,
            master: Master,
            allActors: List[Actor],
            systemPerformance: AllSystemPerformance,
            isContainerMode: bool):
        self.isContainerMode = isContainerMode
        self.systemPerformance = systemPerformance
        self.master = master
        self.nameFactory = NameFactory(nameLogPrinting=master.nameLogPrinting)
        self.user = user
        self.taskList = list(user.application.tasksWithDependency.keys())
        self.taskNameToIndex = self.generateTaskNameToIndex()
        self.allActors = allActors
        self.actorsByTaskName = self.filterActors(allActors)

    def filterActors(self, allActors: List[Actor]) -> Dict[str, List[Actor]]:
        """
         unavailable actors which does not have the required task image
        :param allActors: All registered actor
        :return: a list of available actors. The index of this list is fixed
        and will be used by scheduler
        """
        availableActors = {}
        for taskName in self.taskList:
            imageName = 'fogbus2-%s:latest' % camelToSnake(taskName)
            availableActors[taskName] = []
            if not self.isContainerMode:
                availableActors[taskName] = allActors
                continue
            for actor in allActors:
                if imageName not in actor.actorResources.images:
                    if 'cloudslab/'+ imageName not in \
                            actor.actorResources.images:
                        continue
                availableActors[taskName].append(actor)
            if len(availableActors[taskName]) == 0:
                raise Exception('No available actor for task: ' + taskName)
        return availableActors

    def estimateCost(self, indexSequence: List[int]):
        """
        Estimate the total cost of a chromosome
        :param indexSequence: the index sequence. The value of the this list
        is an int value, which is the index of $availableActors.
        :return: Estimated total cost of the input indexSequence
        """
        individual = self.mapIndexSequenceToActorSequence(indexSequence)
        # For an application, there may be multiple tasks at the entry
        entryCostList = self.entryCost(individual)
        entryCostList = [[cost] for cost in entryCostList]
        for costIndex, task in enumerate(self.user.application.entryTasks):
            # The dependency of an application can be considered as a graph
            # For each entry, use deep first search to find the maximum cost
            # among all the routes
            self.elseCostDFS(
                sourceTask=task,
                individual=individual,
                entryCost=entryCostList,
                currentCost=entryCostList[costIndex][0],
                costIndex=costIndex)
        # find the maximum cost among all the entries
        maximums = [max(costs) for costs in entryCostList]
        return max(maximums)

    def edgeCost(self, sourceComponent: Component, destComponent: Component) \
            -> float:
        sourceKey = sourceComponent.nameConsistent
        if sourceKey not in self.systemPerformance.delay:
            return self.estimateEdgeCost(sourceComponent, destComponent)
        destKey = destComponent.nameConsistent
        if destKey not in self.systemPerformance.delay[sourceKey]:
            return self.estimateEdgeCost(sourceComponent, destComponent)
        return self.systemPerformance.delay[sourceKey][destKey]

    def latencyRoundTrip(
            self, sourceComponent: Component, destComponent: Component) \
            -> float:
        cost = self.edgeLatency(
            sourceComponent=sourceComponent,
            destComponent=destComponent)
        cost += self.edgeLatency(
            sourceComponent=destComponent,
            destComponent=sourceComponent)
        return cost

    def computingCost(
            self, taskExecutor: Component, actor: Actor) -> float:
        nameConsistent = taskExecutor.nameConsistent
        if nameConsistent not in self.systemPerformance.processingTime:
            return self.estimateComputingCost(
                taskExecutor=taskExecutor, actor=actor)
        processingTime = self.systemPerformance.processingTime[nameConsistent]
        return processingTime.processingTime

    def getActor(
            self, individual: List[Actor], task: TaskWithDependency) -> Actor:
        taskIndex = self.taskNameToIndex[task.name]
        actor = individual[taskIndex]
        return actor

    @lru_cache(maxsize=128)
    def sourceToDestCost(
            self,
            sourceComponent: Component,
            destComponent: Component,
            destActor: Union[Actor, None]) -> float:
        edgeCost = self.edgeCost(sourceComponent, destComponent)
        if destActor is None:
            return edgeCost
        computingCost = self.computingCost(
            taskExecutor=destComponent, actor=destActor)
        return edgeCost + computingCost

    def entryCost(self, individual: List[Actor]) -> List[float]:
        entryCostList = []
        for task in self.user.application.entryTasks:
            destComponent, actor = self.convertTask(individual, task)
            stepCost = self.sourceToDestCost(
                sourceComponent=self.master,
                destComponent=destComponent,
                destActor=actor)
            entryCostList.append(stepCost)
        return entryCostList

    def convertTask(
            self, individual: List[Actor], task: TaskWithDependency) \
            -> Union[Tuple[Component, Actor], Tuple[Component, None]]:
        """
        Simulate if the this actor run this task
        :param individual: list of actors
        :param task: task object
        :return: simulated TaskExecutor and the Actor
        """
        if task.name in {'Actuator', 'Sensor'}:
            return self.master, None
        actor = self.getActor(individual=individual, task=task)
        taskExecutor = self.createTaskExecutor(
            user=self.user, actor=actor, task=task)
        return taskExecutor, actor

    def elseCostDFS(
            self,
            sourceTask: Task,
            individual: List[Actor],
            currentCost: float,
            entryCost: List[List[float]],
            costIndex: int):
        """
        A recursive function to find the maximum cost of a graph
        :param sourceTask: the previous task
        :param individual: the chromosome, list of int
        :param currentCost: cost of current recursion
        :param entryCost: a two dimensions list. x is the number of entries,
        y is the cost of each step
        :param costIndex: x
        :return: tail recursion, see www.geeksforgeeks.org/tail-recursion/
        """
        if sourceTask.name == 'Actuator':
            # if this is the end of current route
            entryCost[costIndex].append(currentCost)
            return
        application = self.user.application
        # get sourceTask object
        sourceTask = application.tasksWithDependency[sourceTask.name]
        if not len(sourceTask.children):
            # if there is no more task
            entryCost[costIndex].append(currentCost)
            return
        sourceComponent, actor = self.convertTask(individual, sourceTask)
        for childTask in sourceTask.children:
            # for each child, estimate the cost of this step
            destComponent, destActor = self.convertTask(individual, childTask)
            stepCost = self.sourceToDestCost(
                sourceComponent=sourceComponent,
                destComponent=destComponent,
                destActor=destActor)
            costIncreased = currentCost + stepCost
            # estimate the rest
            self.elseCostDFS(
                sourceTask=childTask,
                individual=individual,
                currentCost=costIncreased,
                entryCost=entryCost,
                costIndex=costIndex)

    def estimateEdgeCost(self, source: Component, dest: Component) -> float:
        """
        estimate the edge cost
        :param source:
        :param dest:
        :return:
        """
        latency = self.edgeLatency(source, dest)
        transmission = self.edgeTransmissionCost(source, dest)
        # edge cost = latency + transmission time
        return latency + transmission

    def edgeLatency(
            self, sourceComponent: Component,
            destComponent: Component) -> float:
        if sourceComponent.hostID not in self.systemPerformance.latency:
            return .1
        if destComponent.hostID not in self.systemPerformance.latency:
            return .1
        return self.systemPerformance.latency[sourceComponent.hostID][
            destComponent.hostID]

    def edgeDataRate(self, source: Component, dest: Component) -> float:
        if source.hostID not in self.systemPerformance.dataRate:
            return .1
        if dest.hostID not in self.systemPerformance.dataRate:
            return .1
        return self.systemPerformance.dataRate[source.hostID][dest.hostID]

    def edgePacketSize(self, source: Component, dest: Component) -> int:
        if source.hostID not in self.systemPerformance.packetSize:
            return 1
        if dest.hostID not in self.systemPerformance.packetSize:
            return 1
        return self.systemPerformance.packetSize[source.hostID][dest.hostID]

    def edgeTransmissionCost(self, source: Component, dest: Component) -> float:
        """
        Estimate the transmission time
        :param source: source component
        :param dest: dest component
        :return:
        """
        packetSize = self.edgePacketSize(source, dest)
        if packetSize == 0:
            return .1
        dataRate = self.edgeDataRate(source, dest)
        if dataRate == 0:
            return .1
        return packetSize / dataRate

    def estimateComputingCost(
            self, taskExecutor: Component, actor: Actor) -> float:
        if taskExecutor.name not in self.systemPerformance.processingTime:
            return .1
        processingTime = self.systemPerformance.processingTime[
            taskExecutor.name]
        resources = processingTime.resources
        dividend = resources.cpu.cores * resources.cpu.frequency
        if dividend == 0:
            return .1
        workload = processingTime.processingTime * dividend
        divider = actor.actorResources.cpu.cores * actor.actorResources.cpu.frequency
        if divider == 0:
            return .1
        estimateProcessingTime = workload / divider
        return estimateProcessingTime

    def mapIndexSequenceToActorSequence(self, indexes: List[int]) \
            -> List[Actor]:
        if len(indexes) is not len(self.taskList):
            raise Exception(
                'Individual length (%d) is not correct (%d)' % (
                    len(indexes), len(self.taskList)))
        actorSequence = [None for _ in range(len(indexes))]
        for j, index in enumerate(indexes):
            taskName = self.taskList[j]
            actorSequence[j] = self.actorsByTaskName[taskName][indexes[j]]
        return actorSequence

    def mapIndexSequenceToHostIDSequence(self, indexes: List[int]) \
            -> List[str]:
        actorSequence = self.mapIndexSequenceToActorSequence(indexes)
        hostIDSequence = self.mapActorSequenceToHostIDSequence(actorSequence)
        return hostIDSequence

    @staticmethod
    def mapActorSequenceToHostIDSequence(actorSequence: List[Actor]) \
            -> List[str]:
        hostIDSequence = [actor.hostID for actor in actorSequence]
        return hostIDSequence

    def mapActorsSequenceToIndexSequence(self, actorSequence: List[Actor]) \
            -> List[int]:
        hostIDSequence = [actor.hostID for actor in actorSequence]
        return self.mapHostIDSequenceToIndexSequence(hostIDSequence)

    def mapHostIDSequenceToIndexSequence(
            self, hostIDSequence: List[str]) -> List[int]:
        if len(hostIDSequence) != len(self.taskList):
            raise Exception(
                'hostIDSequence length (%d) is not correct (%d)' % (
                    len(hostIDSequence), len(self.taskList)))
        indexSequence = [0 for _ in range(len(hostIDSequence))]
        for i, hostID in enumerate(hostIDSequence):
            taskName = self.taskList[i]
            actors = self.actorsByTaskName[taskName]
            indexSequence[i] = self.covertHostIDToIndex(hostID, actors)
        return indexSequence

    @staticmethod
    def covertHostIDToIndex(hostID: str, actors: List[Actor]):
        if not len(actors):
            raise Exception('No available actor')
        for i, actor in enumerate(actors):
            if hostID == actor.hostID:
                return i
        return randint(0, len(actors) - 1)

    def generateTaskNameToIndex(self) -> Dict[str, int]:
        taskNameToIndex = {}
        for i, taskName in enumerate(self.taskList):
            taskNameToIndex[taskName] = i
        return taskNameToIndex

    def createTaskExecutor(
            self, user: User, actor: Actor, task: Task) -> Component:
        name, nameLogPrinting, nameConsistent = \
            self.nameFactory.nameTaskExecutor(
                source=actor,
                taskExecutorID='',
                task=task,
                user=user,
                actor=actor)
        taskExecutor = Component(
            name=name,
            nameLogPrinting=nameLogPrinting,
            nameConsistent=nameConsistent,
            addr=('', 0))
        return taskExecutor
