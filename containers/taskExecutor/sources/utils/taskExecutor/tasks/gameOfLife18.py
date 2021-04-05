from .gameOfLife import GameOfLife


class GameOfLife18(GameOfLife):
    def __init__(self):
        super().__init__(
            60,
            'GameOfLife18',
            ((24, 32), (28, 40)))
