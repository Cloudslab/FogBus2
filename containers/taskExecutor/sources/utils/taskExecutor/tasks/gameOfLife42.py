from .gameOfLife import GameOfLife


class GameOfLife42(GameOfLife):
    def __init__(self):
        super().__init__(
            84,
            'GameOfLife42',
            ((28, 16), (30, 20)))
