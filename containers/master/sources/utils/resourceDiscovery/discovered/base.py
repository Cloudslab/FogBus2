from typing import Tuple

from ...types import ComponentRole


class Discovered(set):

    def __init__(self, role: ComponentRole, portRange: Tuple[int, int]):
        set.__init__(self)
        self.role = role
        self.portRange = portRange
