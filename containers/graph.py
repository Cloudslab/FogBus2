import os
import sys
import json
import numpy as np

from typing import List
from matplotlib import pyplot as plt


class Graph:

    def __init__(
            self,
            logPath: str,
            algorithms: List[str]):
        self.logPath = logPath
        self.algorithms = algorithms
        self.realRespondTime = {}
        self.evaluation = {}

    def run(self):
        self._readEvaluatedRespondTime()
        self._readRealRespondTime()

    def readFromJson(self, filename):
        filename = os.path.join(self.logPath, filename)
        f = open(filename, 'r')
        data = json.load(f)
        f.close()
        return data

    def _readEvaluatedRespondTime(self):
        allFiles = os.listdir(self.logPath)
        evaluation = {}
        for algorithmName in self.algorithms:
            evaluation[algorithmName] = np.empty((10, 100, 200))
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

    def _readRealRespondTime(self):
        allFiles = os.listdir(self.logPath)
        realRespondTime = {}
        for algorithmName in self.algorithms:
            realRespondTime[algorithmName] = np.empty((10, 100))
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
            realRespondTime[algorithmName][roundNum] = np.asarray(data)

        self.realRespondTime = realRespondTime

    def draw(
            self,
            visualData,
            statMethod: str,
            label=''):
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
                if statMethod == 'mean':
                    data = np.mean(visualData[algorithmName], axis=0)
                else:
                    data = np.median(visualData[algorithmName], axis=0)
            ax.plot(x, data)
            algorithms.append(algorithmName)
        ax.legend(algorithms)
        ax.set_ylabel('Respond Time (ms)')
        ax.set_xlabel('Iteration Number')
        statMethod = statMethod[0].upper() + statMethod[1:]

        ax.set_title(
            '%s %s '
            'Respond Time of '
            '%d Rounds' %
            (
                label,
                statMethod,
                roundNum)
        )
        plt.show()

    def drawDiff(self):

        for algorithm in self.algorithms:
            fig, ax = plt.subplots()
            evaluationData = np.mean(self.evaluation[algorithm][:, :, -1], axis=0)
            realData = np.mean(self.realRespondTime[algorithm], axis=0)
            x = [i + 1 for i in range(evaluationData.shape[0])]
            ax.plot(x, evaluationData)
            ax.plot(x, realData)
            ax.legend(['Evaluated', 'Real'])
            ax.set_ylabel('Respond Time (ms)')
            ax.set_xlabel('Iteration Number')
            ax.set_title('Average Evaluated and Real Respond Time \nAgainst Iteration Number for %s' % algorithm)
            plt.show()
        exit()


if __name__ == '__main__':
    resultPath = 'results/10rounds/'
    if len(sys.argv) > 1:
        resultPath = sys.argv[1]
    graph_ = Graph(
        resultPath,
        ['NSGA2', 'NSGA3']
    )
    graph_.run()
    graph_.drawDiff()
    graph_.draw(graph_.realRespondTime, 'mean')
    graph_.draw(graph_.realRespondTime, 'median')
    graph_.draw(graph_.evaluation, 'median', 'Evaluated')
    graph_.draw(graph_.evaluation, 'mean', 'Evaluated')
