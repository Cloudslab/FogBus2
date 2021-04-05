from .base import BaseTask


class GameOfLife(BaseTask):
    def __init__(
            self,
            taskID: int,
            taskName: str,
            focusArea):
        super().__init__(taskID=taskID, taskName=taskName)
        self.world = None
        self.height = None
        self.width = None
        self.focusArea = focusArea

    def adjustFocusArea(self):

        focusArea = [list(point) for point in self.focusArea]
        for i in range(2):
            for j in range(2):
                focusArea[i][j] *= self.height // 32
        self.focusArea = focusArea

    def exec(self, inputData):
        self.world = inputData[0]
        self.height = inputData[1]
        self.width = inputData[2]
        self.adjustFocusArea()
        mayChange = inputData[3]
        newStates = inputData[4]
        mayChangeInNextRound = inputData[5]
        for i, j in mayChange:
            if not self.hitMyFocus(i, j):
                continue
            if self.doesChange(i, j):
                newStates.update([(i, j)])
                neighbours = self.affectedNeighbours(i, j)
                mayChangeInNextRound.update(neighbours)

        return self.world, self.height, self.width, mayChange, newStates, mayChangeInNextRound

    def hitMyFocus(self, i, j) -> bool:
        if i < self.focusArea[0][0]:
            return False
        if i > self.focusArea[1][0]:
            return False
        if j < self.focusArea[0][1]:
            return False
        if j > self.focusArea[1][1]:
            return False
        return True

    def affectedNeighbours(self, i, j):
        neighbours = set([])
        wide = 2
        for iNeighbour in range(i - wide, i + wide):
            for jNeighbour in range(j - wide, j + wide):
                neighbours.update(
                    [(iNeighbour % self.height, jNeighbour % self.width)])
        return neighbours

    def doesChange(self, i, j) -> bool:
        count = self.neighboursCount(i, j)
        if count == 2:
            return False
        if count == 3:
            return not self.world[i][j] == 255
        return not self.world[i][j] == 0

    def neighboursCount(self, i, j):
        count = 0
        neighbours = self.getNeighbours(i, j)
        for i, j in neighbours:
            count += 1 if self.world[i][j] else 0
        return count

    def getNeighbours(self, i, j):
        neighbours = [
            (i - 1, j - 1),
            (i - 1, j),
            (i - 1, (j + 1) % self.width),
            (i, j - 1),
            (i, (j + 1) % self.width),
            ((i + 1) % self.height, j - 1),
            ((i + 1) % self.height, j),
            ((i + 1) % self.height, (j + 1) % self.width)]
        return neighbours
