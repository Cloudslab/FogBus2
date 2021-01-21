import pickle
import traceback
from typing import Dict


def encrypt(obj) -> bytes:
    data = pickle.dumps(obj, 0)
    return data


def decrypt(msg: bytes) -> Dict:
    try:
        obj = pickle.loads(msg, fix_imports=True, encoding="bytes")
        return obj
    except Exception:
        traceback.print_exc()
