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
        self.realData = {}
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
            if algorithmName not in self.evaluation:
                self.evaluation[algorithmName] = np.asarray(data)
                continue
            self.evaluation[algorithmName] = np.vstack((self.evaluation[algorithmName], np.asarray(data)))

    def _readRealRespondTime(self):
        allFiles = os.listdir(self.logPath)
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
            if algorithmName not in self.realData:
                self.realData[algorithmName] = np.asarray(data)
                continue
            self.realData[algorithmName] = np.vstack((self.realData[algorithmName], np.asarray(data)))

    def draw(
            self,
            visulData,
            statMethod: str,
            label=''):
        if not len(self.realData):
            return
        roundNum = 0
        rangeNum = 0
        for data in visulData.values():
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
        for algorithmName, data in visulData.items():
            if len(visulData[algorithmName].shape) == 1:
                data = visulData[algorithmName]
            else:
                if statMethod == 'mean':
                    data = np.mean(visulData[algorithmName], axis=0)
                else:
                    data = np.median(visulData[algorithmName], axis=0)
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


if __name__ == '__main__':
    resultPath = 'results/10rounds/'
    if len(sys.argv) > 1:
        resultPath = sys.argv[1]
    graph_ = Graph(
        resultPath,
        ['NSGA2', 'NSGA3']
    )
    graph_.run()
    graph_.draw(graph_.realData, 'mean')
    graph_.draw(graph_.realData, 'median')
    graph_.draw(graph_.evaluation, 'median', 'Evaluated')
    graph_.draw(graph_.evaluation, 'mean', 'Evaluated')
