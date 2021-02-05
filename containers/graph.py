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
        self.data = {}

    def run(self):
        self._readLogs()

    def _readLogs(self):
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
            filename = os.path.join(self.logPath, file)
            f = open(filename, 'r')
            data = json.load(f)
            f.close()
            if algorithmName not in self.data:
                self.data[algorithmName] = np.asarray(data)
                continue
            self.data[algorithmName] = np.vstack((self.data[algorithmName], np.asarray(data)))

    def draw(self, statMethod: str):
        if not len(self.data):
            return
        roundNum = 0
        rangeNum = 0
        for data in self.data.values():
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
        for algorithmName, data in self.data.items():
            if len(self.data[algorithmName].shape) == 1:
                data = self.data[algorithmName]
            else:
                if statMethod == 'mean':
                    data = np.mean(self.data[algorithmName], axis=0)
                else:
                    data = np.median(self.data[algorithmName], axis=0)
            ax.plot(x, data)
            algorithms.append(algorithmName)
        ax.legend(algorithms)
        ax.set_ylabel('Respond Time (ms)')
        ax.set_xlabel('Iteration Number')
        statMethod = statMethod[0].upper() + statMethod[1:]

        ax.set_title(
            '%s Delays of %d Rounds' %
            (statMethod, roundNum)
        )
        plt.show()


if __name__ == '__main__':
    resultPath = './'
    if len(sys.argv) > 1:
        resultPath = sys.argv[1]
    graph_ = Graph(
        resultPath,
        ['NSGA2', 'NSGA3']
    )
    graph_.run()
    graph_.draw('mean')
    graph_.draw('median')
