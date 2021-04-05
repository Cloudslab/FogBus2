from threading import Lock
from typing import Dict
from typing import List
from typing import Tuple
from typing import Union

from ....types import Address
from ....types import Component

MapUnion = Union[str, str, Address]
MapTuple = Tuple[str, str, Address]


class Registered:

    def __init__(self):
        self.lock: Lock = Lock()
        self.len = 0
        self.dict = {}
        self.allItems = set()
        self.keyMap: Dict[MapUnion, MapTuple] = {}

    def copyAll(self) -> List:
        return list(self.allItems)

    def __len__(self):
        return self._len()

    def __setitem__(self, key, component):
        self._setitem(key=key, component=component)

    def __getitem__(self, key):
        return self._getitem(key=key)

    def __delitem__(self, key):
        self._delitem(key=key)

    def __contains__(self, component) -> bool:
        return self._contains(component)

    def _len(self):
        self.lock.acquire()
        ret = len(self.allItems)
        self.lock.release()
        return ret

    def _setitem(self, key, component):
        self.lock.acquire()
        componentID = component.componentID
        nameConsistent = component.nameConsistent
        addr = component.addr
        self.dict.__setitem__(componentID, component)
        self.dict.__setitem__(nameConsistent, component)
        self.dict.__setitem__(addr, component)
        t = (componentID, nameConsistent, addr)
        self.keyMap[componentID] = t
        self.keyMap[nameConsistent] = t
        self.keyMap[addr] = t
        self.allItems.add(component)
        self.lock.release()

    def _getitem(self, key):
        try:
            self.lock.acquire()
            component = self.dict[key]
            self.lock.release()
            return component
        except KeyError:
            self.lock.release()
            raise KeyError

    def _delitem(self, key):
        self.lock.acquire()
        if key not in self.dict:
            self.lock.release()
            return
        componentID, nameConsistent, addr = self.keyMap[key]
        component = self.dict[key]
        self.allItems.remove(component)
        try:
            del self.dict[componentID]
            del self.dict[nameConsistent]
            del self.dict[addr]
            del self.keyMap[componentID]
            del self.keyMap[nameConsistent]
            del self.keyMap[addr]
        except KeyError:
            pass
        self.lock.release()

    def _contains(self, component) -> bool:
        ret = False
        self.lock.acquire()
        if isinstance(component, str):
            if component in self.dict:
                ret = True
            self.lock.release()
            return ret
        if not isinstance(component, Component):
            self.lock.release()
            return False
        elif component.componentID in self.dict:
            ret = True
        elif component.nameConsistent in self.dict:
            ret = True
        elif component.addr in self.dict:
            ret = True
        self.lock.release()
        return ret
