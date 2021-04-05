from pickle import loads
from traceback import print_exc
from typing import Dict


def decrypt(msg: bytes) -> Dict:
    try:
        obj = loads(msg, fix_imports=True, encoding="bytes")
        return obj
    except Exception:
        print_exc()
