import os
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
        fig, ax = plt.subplots()
        # fig.ylabel('Respond Time (ms)')
        x = [i for i in range(1, 36)]
        algorithms = []
        for algorithmName, data in self.data.items():
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
            '%s Delays of 10 Rounds' %
            statMethod
        )
        plt.show()


if __name__ == '__main__':
    graph_ = Graph(
        'results',
        ['NSGA2', 'NSGA3']
    )
    graph_.run()
    graph_.draw('mean')
    graph_.draw('median')
