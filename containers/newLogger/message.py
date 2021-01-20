import pickle
from typing import Any


def encrypt(obj) -> bytes:
    data = pickle.dumps(obj, 0)
    return data


def decrypt(msg) -> Any:
    obj = pickle.loads(msg, fix_imports=True, encoding="bytes")
    return obj
