from .gameOfLifeParallelized import GameOfLifeParallelized
from .gameOfLifeSerialized import GameOfLifeSerialized
from ...component.basic import BasicComponent


class GameOfLifePyramid(GameOfLifeParallelized):
    def __init__(
            self,
            videoPath: str,
            targetHeight: int,
            showWindow: bool,
            basicComponent: BasicComponent,
            golInitText: str):
        GameOfLifeSerialized.__init__(
            self,
            appName='GameOfLifePyramid',
            videoPath=videoPath,
            targetHeight=targetHeight,
            showWindow=showWindow,
            basicComponent=basicComponent,
            golInitText=golInitText)
        self.resCountThreshold = 32
