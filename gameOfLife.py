import cv2
import numpy as np
from time import time, sleep


class GameOfLife:
    def __init__(
            self,
            height=512,
            width=1024,
            generationNumber=None,
            fps=60,
            resizeFactor=8):
        self.__resizeFactor = resizeFactor
        self.height = height // self.__resizeFactor
        self.width = width // self.__resizeFactor
        self.generationNumber = generationNumber
        self.boundaries = [[0, 0], [self.height, self.width]]
        self.world = np.zeros((self.height, self.width, 1), np.uint8)
        self.newStates = []
        self.frameUpdateGap = 1 / fps

    def examplePoints(self, ):
        i, j = self.height // 2, self.width // 2
        points = [(i, j)]

        for k in range(10):
            points.append((i + k, j))
        for k in range(1, 5):
            points.append((i, j + k))
            points.append((i + 4, j + k))
        return points

    def startWithText(self, text):
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

        cv2.imshow(
            'Game of Life',
            cv2.resize(
                self.world,
                (self.width * self.__resizeFactor,
                 self.height * self.__resizeFactor),
                interpolation=cv2.INTER_AREA))
        print('[*] This is your initial world. Press \'Space\' to start.')
        cv2.waitKey(0)

    def updateBoundaries(self, i, j):
        # change boundaries
        if i <= self.boundaries[0][0]:
            self.boundaries[0][0] = i - 1
        elif i >= self.boundaries[1][0]:
            self.boundaries[1][0] = (i + 1) % self.width
        if j <= self.boundaries[0][1]:
            self.boundaries[0][1] = (j - 1) % self.height
        elif j >= self.boundaries[1][1]:
            self.boundaries[1][1] = j + 1

    def run(self):
        gen = 0
        preUpdateTime = time()
        count = 10
        while True:
            cv2.imshow(
                'Game of Life',
                cv2.resize(
                    self.world,
                    (self.width * self.__resizeFactor,
                     self.height * self.__resizeFactor),
                    interpolation=cv2.INTER_AREA))
            # cv2.waitKey(0)
            if cv2.waitKey(1) == ord('q'):
                break
            self.move()
            self.changeStates()
            gen += 1
            print('\r[*] Generation %d' % gen, end='')
            if count >= 0:
                count -= 1
                sleep(2)
                continue
            timeDiff = time() - preUpdateTime
            if timeDiff < self.frameUpdateGap:
                sleep(self.frameUpdateGap - timeDiff)
            if self.generationNumber is None:
                continue
            elif gen == self.generationNumber:
                break

    def move(self):
        for i in range(0, self.height):
            for j in range(0, self.width):
                if self.doesChange(self.world, i, j):
                    self.newStates.append((i, j))
                    self.updateBoundaries(i, j)

    def changeStates(self):
        for i, j in self.newStates:
            if self.world[i % self.height][j % self.width] == 0:
                self.world[i % self.height][j % self.width] = 255
            else:
                self.world[i % self.height][j % self.width] = 0
        self.newStates = []

    def doesChange(self, world, i, j) -> bool:
        count = self.neighboursCount(world, i, j)
        if count == 2:
            return False
        if count == 3:
            return not world[i % self.height][j % self.width] == 255
        return not world[i % self.height][j % self.width] == 0

    def neighboursCount(self, world, i, j):
        count = 0
        count += 1 if world[i - 1][j - 1] else 0
        count += 1 if world[i - 1][j % self.width] else 0
        count += 1 if world[i - 1][(j + 1) % self.width] else 0
        count += 1 if world[i % self.height][j - 1] else 0
        count += 1 if world[i % self.height][(j + 1) % self.width] else 0
        count += 1 if world[(i + 1) % self.height][j - 1] else 0
        count += 1 if world[(i + 1) % self.height][j % self.width] else 0
        count += 1 if world[(i + 1) % self.height][(j + 1) % self.width] else 0
        return count


if __name__ == '__main__':
    game = GameOfLife(
        height=1024,
        width=2048,
        resizeFactor=3)
    game.startWithText('Qifan Deng')
    # game.setPoints(game.examplePoints())
    game.run()
