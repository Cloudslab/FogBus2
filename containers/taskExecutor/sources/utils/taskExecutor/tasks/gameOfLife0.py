from .gameOfLife import GameOfLife


class GameOfLife0(GameOfLife):
    def __init__(self):
        super().__init__(
            42,
            'GameOfLife0',
            ((0, 0), (16, 32)))
