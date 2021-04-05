from typing import Union

from .base import Registered
from ..roles import Master

MasterKey = Union[Master, str]


class RegisteredMasters(Registered):
    pass

    def __setitem__(self, key, master: Master):
        return self._setitem(key=key, component=master)

    def __contains__(self, masterOrStr: MasterKey):
        return self._contains(masterOrStr)

    def __getitem__(self, key: MasterKey) -> Master:
        return self._getitem(key)
