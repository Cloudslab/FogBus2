from .gameOfLife import GameOfLife


class GameOfLife28(GameOfLife):
    def __init__(self):
        super().__init__(
            70,
            'GameOfLife28',
            ((30, 36), (32, 38)))
