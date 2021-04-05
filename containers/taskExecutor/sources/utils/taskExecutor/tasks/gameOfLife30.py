from .gameOfLife import GameOfLife


class GameOfLife30(GameOfLife):
    def __init__(self):
        super().__init__(
            72,
            'GameOfLife30',
            ((30, 32), (32, 34)))
