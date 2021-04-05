from .gameOfLife import GameOfLife


class GameOfLife33(GameOfLife):
    def __init__(self):
        super().__init__(
            75,
            'GameOfLife33',
            ((16, 16), (24, 32)))
