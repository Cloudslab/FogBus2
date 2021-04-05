from .gameOfLife import GameOfLife


class GameOfLife3(GameOfLife):
    def __init__(self):
        super().__init__(
            45,
            'GameOfLife3',
            ((16, 48), (24, 64)))
