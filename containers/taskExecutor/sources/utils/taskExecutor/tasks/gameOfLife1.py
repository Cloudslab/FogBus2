from .gameOfLife import GameOfLife


class GameOfLife1(GameOfLife):
    def __init__(self):
        super().__init__(
            43,
            'GameOfLife1',
            ((0, 32), (16, 64)))
