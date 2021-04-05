import json
import os
import sys
from typing import List

import numpy as np
from matplotlib import pyplot as plt


class Graph:

    def __init__(
            self,
            logPath: str,
            algorithms: List[str],
            roundNum,
            iterationEachRound,
            iterationOfGA):
        self.logPath = logPath
        self.algorithms = algorithms
        self.realResponseTime = {}
        self.evaluation = {}
        self.roundNum = roundNum
        self.iterationEachRound = iterationEachRound
        self.iterationOfGA = iterationOfGA

    def run(self):
        self._readEstimatedResponseTime()
        self._readRealResponseTime()

    def readFromJson(self, filename):
        filename = os.path.join(self.logPath, filename)
        f = open(filename, 'r')
        data = json.load(f)
        f.close()
        return data

    def _readEstimatedResponseTime(self):
        allFiles = os.listdir(self.logPath)
        evaluation = {}
        for algorithmName in self.algorithms:
            evaluation[algorithmName] = np.empty(
                (self.roundNum, self.iterationEachRound, self.iterationOfGA))
        for file in allFiles:
            if os.path.isdir(file):
                continue
            parts = file.split('-')
            if len(parts) != 4:
                continue
            if parts[0] != 'Evaluation':
                continue
            algorithmName = parts[1]
            if algorithmName not in self.algorithms:
                continue
            data = self.readFromJson(file)
            roundNum = int(parts[2]) - 1
            iterationNum = int(parts[3].split('.')[0])

            evaluation[algorithmName][roundNum][iterationNum] = np.asarray(data)
        self.evaluation = evaluation

    def _readRealResponseTime(self):
        allFiles = os.listdir(self.logPath)
        realResponseTime = {}
        for algorithmName in self.algorithms:
            realResponseTime[algorithmName] = np.empty(
                (self.roundNum, self.iterationEachRound))
        for file in allFiles:
            if os.path.isdir(file):
                continue
            parts = file.split('-')
            if len(parts) != 2:
                continue
            algorithmName = parts[0]
            if algorithmName not in self.algorithms:
                continue
            data = self.readFromJson(file)
            roundNum = int(parts[1].split('.')[0]) - 1
            realResponseTime[algorithmName][roundNum] = np.asarray(data)

        self.realResponseTime = realResponseTime

    def draw(
            self,
            visualData, ):
        if not len(visualData):
            return
        roundNum = 0
        rangeNum = 0
        for data in visualData.values():
            if len(data.shape) == 1:
                roundNum = 1
                rangeNum = data.shape[0]
            else:
                roundNum = data.shape[0]
                rangeNum = data.shape[1]
            break
        if roundNum == 0:
            return

        fig, ax = plt.subplots()
        # fig.ylabel('Respond Time (ms)')
        x = [i for i in range(1, rangeNum + 1)]
        algorithms = []
        for algorithmName, data in visualData.items():
            if len(visualData[algorithmName].shape) == 1:
                data = visualData[algorithmName]
            else:
                # if statMethod == 'mean':
                #     data = np.mean(visualData[algorithmName], axis=0)
                # else:
                data = np.median(visualData[algorithmName], axis=0)
            ax.plot(x, data)
            algorithms.append(algorithmName)
        ax.legend(algorithms)
        ax.set_ylabel('Respond Time (ms)')
        ax.set_xlabel('User Request Number')
        title = 'Real Respond Time \n' \
                'on Average ' \
                'of %d Rounds' % roundNum
        ax.set_title(title)
        self.saveToFile(title)
        plt.show()

    def drawDiff(self):

        for algorithm in self.algorithms:
            fig, ax = plt.subplots()
            evaluationData = np.mean(self.evaluation[algorithm][:, :, -1],
                                     axis=0)
            realData = np.mean(self.realResponseTime[algorithm], axis=0)
            x = [i + 1 for i in range(evaluationData.shape[0])]
            ax.plot(x, evaluationData)
            ax.plot(x, realData)
            ax.legend(['Estimated', 'Real'])
            ax.set_ylabel('Respond Time (ms)')
            ax.set_xlabel('User Request Number')
            title = 'Estimated and Real Respond Time \n' \
                    'on Average ' \
                    'of %s' % algorithm
            ax.set_title(title)
            self.saveToFile(title)
            plt.show()

    def drawConvergence(self):
        fig, ax = plt.subplots()
        for algorithm, evaluationData in self.evaluation.items():
            shape = evaluationData.shape
            reshapedData = evaluationData.reshape(
                (shape[0] * shape[1], shape[2]))
            meanData = np.mean(reshapedData, axis=0)
            x = [i + 1 for i in range(meanData.shape[0])]
            ax.plot(x, meanData)

        ax.legend(self.evaluation.keys())
        ax.set_ylabel('Respond Time (ms)')
        ax.set_xlabel(
            'Iteration Number (Generation Number of Genetic Algorithm)')
        title = 'Estimated Respond Time \n' \
                'on Average '
        ax.set_title(title)
        self.saveToFile(title)
        plt.show()

    def drawConvergenceForInitWithLog(self):
        fig, ax = plt.subplots()
        for algorithm, evaluationData in self.evaluation.items():
            shape = evaluationData.shape
            reshapedData = evaluationData.reshape(
                (shape[0] * shape[1], shape[2]))
            meanData = np.mean(reshapedData, axis=0)
            x = [i + 1 for i in range(meanData.shape[0])]
            ax.plot(x, meanData)

        ax.legend(self.evaluation.keys())
        ax.set_ylabel('Respond Time (ms)')
        ax.set_xlabel(
            'Iteration Number (Generation Number of Genetic Algorithm)')
        title = 'Estimated Respond Time on Average'
        ax.set_title(title)
        self.saveToFile(title)
        plt.show()

    @staticmethod
    def saveToFile(filename):
        graphPath = 'results/graph'
        filename = os.path.join(graphPath, filename)
        plt.savefig(filename)


def testNSGA2AndNSGA3():
    resultPath = 'results/final/excel'
    if len(sys.argv) > 1:
        resultPath = sys.argv[1]
    graph_ = Graph(
        resultPath,
        [
            'NSGA2',
            'NSGA3',
            'NSGA2InitWithLog'
        ],
        1,
        100,
        200)
    graph_.run()
    graph_.drawConvergence()
    graph_.drawDiff()
    graph_.draw(graph_.realResponseTime)


def testInitWithLog():
    resultPath = 'results/final/excel'
    if len(sys.argv) > 1:
        resultPath = sys.argv[1]
    graph_ = Graph(
        resultPath,
        [
            'NSGA2',
            'NSGA3',
            'NSGA2InitWithLog'
        ],
        1,
        100,
        200)
    graph_.run()
    graph_.drawConvergenceForInitWithLog()


if __name__ == '__main__':
    testNSGA2AndNSGA3()
    testInitWithLog()
