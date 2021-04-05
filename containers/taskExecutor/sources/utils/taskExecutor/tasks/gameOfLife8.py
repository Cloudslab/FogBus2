from .gameOfLife import GameOfLife


class GameOfLife8(GameOfLife):
    def __init__(self):
        super().__init__(
            50,
            'GameOfLife8',
            ((30, 60), (32, 62)))
