from typing import Any
from typing import Callable
from typing import Dict


class LoopSourceDestination:

    def __init__(self, f):
        pass

    def __call__(self, *args, **kwargs):
        dictInDict: Dict[str, Dict[str, Any]] = kwargs['dictInDict']
        runner: Callable = kwargs['runner']
        for source, destinations in dictInDict.items():
            for destination, data in destinations.items():
                runner(source, destination, data)
