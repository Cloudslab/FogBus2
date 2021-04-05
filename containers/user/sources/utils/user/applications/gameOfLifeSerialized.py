from time import time

import cv2
import numpy as np

from .base import ApplicationUserSide
from ...component.basic import BasicComponent


class GameOfLifeSerialized(ApplicationUserSide):

    def __init__(
            self,
            videoPath: str,
            targetHeight: int,
            showWindow: bool,
            basicComponent: BasicComponent,
            golInitText: str,
            appName: str = 'GameOfLifeSerialized'):
        super().__init__(
            appName=appName,
            videoPath=videoPath,
            targetHeight=targetHeight,
            showWindow=showWindow,
            basicComponent=basicComponent,
            pressSpaceToStart=True)
        t = self.targetHeight // 128 * 128

        self._resizeFactor = 4
        self.height = t // self._resizeFactor
        self.width = t * 2 // self._resizeFactor
        self.generationNumber = None
        self.world = np.zeros((self.height, self.width, 1), np.uint8)
        self.newStates = set([])
        self.frameUpdateGap = 1 / 60
        self.mayChange = set([])
        self.golInitText = golInitText

    def prepare(self):
        pass

    def show(self, gen: int):
        if self._resizeFactor != 1:
            showWorld = cv2.resize(
                self.world,
                (self.width * self._resizeFactor,
                 self.height * self._resizeFactor),
                interpolation=cv2.INTER_AREA)
        else:
            showWorld = self.world

        if self.showWindow:
            self.windowFrameQueue.put((self.appName, showWorld))
        self.basicComponent.debugLogger.info('[*] Generation %d' % gen)

        if not self.showWindow:
            return
        if gen != 0:
            return
        self.basicComponent.debugLogger.info(
            '[*] This is your initial world. Press \'Space\' to start.')

    def _run(self):
        self.startWithText()
        self.show(0)
        self.canStart.wait()
        self.basicComponent.debugLogger.info(
            'Application is running: %s', self.appName)
        gen = 0
        while True:
            gen += 1
            self.show(gen)
            inputData = (
                self.world,
                self.height,
                self.width,
                self.mayChange,
                set([]),
                set([]))
            self.dataToSubmit.put(inputData)
            lastDataSentTime = time()
            result = self.resultForActuator.get()
            responseTime = (time() - lastDataSentTime) * 1000
            self.responseTime.update(responseTime)
            self.responseTimeCount += 1
            self.newStates.update(result[4])
            self.mayChange.update(result[5])
            self.changeStates()

    def startWithText(self):
        text = self.golInitText
        color = (255, 0, 0)
        textSize = cv2.getTextSize(text, 0, 1, 2)[0]
        positionX = (self.world.shape[1] - textSize[0]) // 2
        positionY = (self.world.shape[0] + textSize[1]) // 2
        world = cv2.putText(
            self.world,
            text,
            (positionX, positionY),
            0,
            1,
            color,
            1,
            cv2.LINE_AA)
        _, self.world = cv2.threshold(world, 127, 255, cv2.THRESH_BINARY)
        self.initMayChange(theWholeWorld=True)
        if self.showWindow:
            frame = cv2.resize(
                self.world,
                (self.width * self._resizeFactor,
                 self.height * self._resizeFactor),
                interpolation=cv2.INTER_AREA)
            self.windowFrameQueue.put((self.appName, frame))

    def initMayChange(self, theWholeWorld=False):
        self.mayChange = set([])
        for i in range(0, self.height):
            for j in range(0, self.width):
                if theWholeWorld:
                    self.mayChange.update([(i, j)])
                    continue
                if not self.doesChange(i, j):
                    continue
                neighbours = self.affectedNeighbours(i, j)
                self.mayChange.update(neighbours)

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

    def affectedNeighbours(self, i, j):
        neighbours = set([])
        wide = 2
        for iNeighbour in range(i - wide, i + wide):
            for jNeighbour in range(j - wide, j + wide):
                neighbours.update(
                    [(iNeighbour % self.height, jNeighbour % self.width)])
        return neighbours

    def changeStates(self):
        for i, j in self.newStates:
            if self.world[i][j] == 0:
                self.world[i][j] = 255
                continue
            self.world[i][j] = 0
        self.newStates = set([])
