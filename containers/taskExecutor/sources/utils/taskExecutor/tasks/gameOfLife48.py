from .gameOfLife import GameOfLife


class GameOfLife48(GameOfLife):
    def __init__(self):
        super().__init__(
            90,
            'GameOfLife48',
            ((24, 0), (28, 8)))
