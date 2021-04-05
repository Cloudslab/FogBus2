from typing import Dict
from typing import Tuple
from typing import Union

from .base import Registered
from ..roles import Actor
from ....types import Address
from ....types import Component

ActorKey = Union[Actor, str]

MapUnion = Union[str, str, str, Address]
MapTuple = Tuple[str, str, str, Address]


class RegisteredActors(Registered):

    def __init__(self):

        super().__init__()
        self.keyMap: Dict[MapUnion, MapTuple] = {}

    def __setitem__(self, key, actor: Actor):
        return self._setitem(key=key, actor=actor)

    def __contains__(self, actorOrStr: ActorKey):
        return self._contains(actorOrStr)

    def __getitem__(self, key: ActorKey) -> Actor:
        return self._getitem(key)

    def _setitem(self, key, actor: Actor):
        self.lock.acquire()
        componentID = actor.componentID
        nameConsistent = actor.nameConsistent
        addr = actor.addr
        hostID = actor.hostID
        self.dict.__setitem__(componentID, actor)
        self.dict.__setitem__(nameConsistent, actor)
        self.dict.__setitem__(addr, actor)
        self.dict.__setitem__(hostID, actor)
        self.dict.__setitem__(actor, actor)
        t = (hostID, componentID, nameConsistent, addr)
        self.keyMap[hostID] = t
        self.keyMap[componentID] = t
        self.keyMap[nameConsistent] = t
        self.keyMap[addr] = t
        self.allItems.add(actor)
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
        hostID, componentID, nameConsistent, addr = self.keyMap[key]
        component = self.dict[key]
        self.allItems.remove(component)
        try:
            del self.dict[componentID]
            del self.dict[nameConsistent]
            del self.dict[addr]
            del self.dict[hostID]
            del self.keyMap[componentID]
            del self.keyMap[nameConsistent]
            del self.keyMap[addr]
            del self.keyMap[hostID]
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
        if component.hostID in self.dict:
            ret = True
        elif component.componentID in self.dict:
            ret = True
        elif component.nameConsistent in self.dict:
            ret = True
        elif component.addr in self.dict:
            ret = True
        self.lock.release()
        return ret
