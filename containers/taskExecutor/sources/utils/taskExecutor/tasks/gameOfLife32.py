from .gameOfLife import GameOfLife


class GameOfLife32(GameOfLife):
    def __init__(self):
        super().__init__(
            74,
            'GameOfLife32',
            ((16, 0), (24, 16)))
