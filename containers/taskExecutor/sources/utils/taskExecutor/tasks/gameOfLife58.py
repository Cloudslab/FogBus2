from .gameOfLife import GameOfLife


class GameOfLife58(GameOfLife):
    def __init__(self):
        super().__init__(
            100,
            'GameOfLife58',
            ((30, 4), (32, 6)))
