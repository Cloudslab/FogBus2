import csv
from collections import defaultdict
from typing import Dict
from typing import List

from dependencies import Application
from dependencies import loadDependencies
from dependencies import Task


class Weight:

    def __init__(self, app: Application, resolution: int):
        self.app: Application = app
        self.resolution: int = resolution


class EdgeWeight(Weight):

    def __init__(
            self,
            app: Application,
            resolution: int,
            source: str,
            destination: str,
            medianReceivedPackageSize: float,
            medianSentPackageSize: float,
            lowestReceivingSpeed: float,
            highestReceivingSpeed: float,
            lowestSendingSpeed: float,
            highestSendingSpeed: float):
        super().__init__(app, resolution)
        self.source = source
        self.destination = destination
        self.medianReceivedPackageSize = medianReceivedPackageSize
        self.medianSentPackageSize = medianSentPackageSize
        self.lowestReceivingSpeed = lowestReceivingSpeed
        self.highestReceivingSpeed = highestReceivingSpeed
        self.lowestSendingSpeed = lowestSendingSpeed
        self.highestSendingSpeed = highestSendingSpeed


class EdgeWeightLookup:

    def __init__(self, edgeWeights: List[EdgeWeight]):
        self.__edgeWeightsDict = defaultdict(
            lambda: defaultdict(lambda: defaultdict(EdgeWeight)))

        for edgeWeight in edgeWeights:
            self.__edgeWeightsDict[edgeWeight.app.name][edgeWeight.source][
                edgeWeight.destination] = edgeWeight

    def __getitem__(self, item):
        return self.__edgeWeightsDict[item]


class EdgeWeights:

    def __init__(self, edgeWeights: List[EdgeWeight]):
        self.__edgeWeightsList: List[EdgeWeight] = edgeWeights
        self.__edgeWeightsLookup: EdgeWeightLookup = EdgeWeightLookup(
            edgeWeights)

    def __getitem__(self, item):
        return self.__edgeWeightsLookup[item]

    def __iter__(self):
        next(self.__edgeWeightsList)


def loadEdgeWeights(applications: Dict[str, Application]) -> EdgeWeights:
    edgeWeights = []
    with open('profiler/weightsOfEdges.csv', newline='') as file:
        reader = csv.reader(file, delimiter=',')
        next(reader)
        for row in reader:
            edgeWeight = EdgeWeight(
                app=applications[row[0]],
                resolution=int(row[1][:-1]),
                source=row[2],
                destination=row[3],
                medianReceivedPackageSize=float(row[4]),
                medianSentPackageSize=float(row[5]),
                lowestReceivingSpeed=float(row[6]),
                highestReceivingSpeed=float(row[7]),
                lowestSendingSpeed=float(row[8]),
                highestSendingSpeed=float(row[9]))

            edgeWeights.append(edgeWeight)
        file.close()

    return EdgeWeights(edgeWeights=edgeWeights)


class TaskWeight(Weight):

    def __init__(
            self,
            app: Application,
            resolution: int,
            task: Task,
            medianProcessingTime: float,
            medianCalls: float,
            CPUFrequency: float, ):
        super().__init__(app, resolution)
        self.task: Task = task
        self.medianProcessingTime = medianProcessingTime
        self.medianCalls = medianCalls
        self.CPUFrequency = CPUFrequency


class TaskWeightLookup:

    def __init__(self, taskWeights: List[TaskWeight]):
        self.__taskWeightsDict = defaultdict(lambda: defaultdict(EdgeWeight))

        for taskWeight in taskWeights:
            self.__taskWeightsDict[taskWeight.app.name][
                taskWeight.task.name] = taskWeight

    def __getitem__(self, item):
        return self.__taskWeightsDict[item]


class TaskWeights(Weight):

    def __init__(self, taskWeights: List[TaskWeight]):
        self.__taskWeightsList: List[TaskWeight] = taskWeights
        self.__edgeWeightsLookup: TaskWeightLookup = TaskWeightLookup(
            taskWeights)

    def __getitem__(self, item):
        return self.__edgeWeightsLookup[item]

    def __iter__(self):
        next(self.__taskWeightsList)


def loadTaskWeights(tasks: Dict[str, Task],
                    applications: Dict[str, Application]):
    taskWeights = []
    with open('profiler/weightsOfTasks.csv', newline='') as file:
        reader = csv.reader(file, delimiter=',')
        next(reader)
        for row in reader:
            taskWeight = TaskWeight(
                app=applications[row[0]],
                resolution=int(row[1][:-1]),
                task=tasks[row[2]],
                medianProcessingTime=float(row[3]),
                medianCalls=float(row[4]),
                CPUFrequency=float(row[5]))

            taskWeights.append(taskWeight)
        file.close()

    return TaskWeights(taskWeights)


if __name__ == '__main__':
    tasks_, applications_ = loadDependencies()
    edgeWeights_ = loadEdgeWeights(applications_)
    taskWeights_ = loadTaskWeights(tasks_, applications_)
