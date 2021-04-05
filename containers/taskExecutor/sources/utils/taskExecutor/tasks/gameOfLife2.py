from .gameOfLife import GameOfLife


class GameOfLife2(GameOfLife):
    def __init__(self):
        super().__init__(
            44,
            'GameOfLife2',
            ((16, 32), (24, 48)))
