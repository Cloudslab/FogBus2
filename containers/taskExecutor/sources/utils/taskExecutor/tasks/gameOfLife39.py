from .gameOfLife import GameOfLife


class GameOfLife39(GameOfLife):
    def __init__(self):
        super().__init__(
            81,
            'GameOfLife39',
            ((30, 30), (32, 32)))
