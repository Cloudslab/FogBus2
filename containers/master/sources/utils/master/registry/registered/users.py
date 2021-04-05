from typing import Union

from .base import Registered
from ..roles import User

UserKey = Union[User, str]


class RegisteredUsers(Registered):
    pass

    def __setitem__(self, key, user: User):
        return self._setitem(key=key, component=user)

    def __contains__(self, userOrStr: UserKey):
        return self._contains(userOrStr)

    def __getitem__(self, key: UserKey) -> User:
        return self._getitem(key)
