from typing import List

import numpy as np


def randomPopulation(
        lowerBounds: List[int],
        upperBounds: List[int],
        variableNum: int,
        populationSize: int):
    matrix = np.zeros(
        shape=(variableNum, populationSize),
        dtype=np.int)

    for i in range(variableNum):
        column = np.random.randint(
            low=lowerBounds[i],
            high=upperBounds[i] + 1,
            size=populationSize)
        matrix[i] = column
    indexSequencesRandom = np.transpose(matrix)
    return indexSequencesRandom
