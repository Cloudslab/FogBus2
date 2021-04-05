from .gameOfLife import GameOfLife


class GameOfLife24(GameOfLife):
    def __init__(self):
        super().__init__(
            66,
            'GameOfLife24',
            ((30, 40), (32, 42)))
