from .gameOfLife import GameOfLife


class GameOfLife60(GameOfLife):
    def __init__(self):
        super().__init__(
            102,
            'GameOfLife60',
            ((30, 0), (32, 2)))
