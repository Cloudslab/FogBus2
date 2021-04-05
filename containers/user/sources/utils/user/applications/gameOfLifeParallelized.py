from time import time

from .gameOfLifeSerialized import GameOfLifeSerialized
from ...component.basic import BasicComponent


class GameOfLifeParallelized(GameOfLifeSerialized):

    def __init__(
            self,
            videoPath: str,
            targetHeight: int,
            showWindow: bool,
            basicComponent: BasicComponent,
            golInitText: str):
        GameOfLifeSerialized.__init__(
            self,
            appName='GameOfLifeParallelized',
            videoPath=videoPath,
            targetHeight=targetHeight,
            showWindow=showWindow,
            basicComponent=basicComponent,
            golInitText=golInitText)
        self.resCountThreshold = 62

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
            resCount = 0
            self.newStates = set([])
            self.mayChange = set([])
            while resCount < self.resCountThreshold:
                result = self.resultForActuator.get()
                resCount += 1
                self.newStates.update(result[4])
                self.mayChange.update(result[5])
            respondTime = (time() - lastDataSentTime) * 1000
            self.responseTime.update(respondTime)
            self.responseTimeCount += 1
            self.changeStates()
