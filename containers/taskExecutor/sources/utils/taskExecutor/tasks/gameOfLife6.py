from .gameOfLife import GameOfLife


class GameOfLife6(GameOfLife):
    def __init__(self):
        super().__init__(
            48,
            'GameOfLife6',
            ((28, 56), (30, 60)))
