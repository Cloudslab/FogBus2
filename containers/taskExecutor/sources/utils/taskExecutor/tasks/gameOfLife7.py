from .gameOfLife import GameOfLife


class GameOfLife7(GameOfLife):
    def __init__(self):
        super().__init__(
            49,
            'GameOfLife7',
            ((28, 60), (30, 64)))
