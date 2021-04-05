from .gameOfLife import GameOfLife


class GameOfLife9(GameOfLife):
    def __init__(self):
        super().__init__(
            51,
            'GameOfLife9',
            ((30, 62), (32, 64)))
