from .gameOfLife import GameOfLife


class GameOfLife16(GameOfLife):
    def __init__(self):
        super().__init__(
            58,
            'GameOfLife16',
            ((30, 48), (32, 50)))
