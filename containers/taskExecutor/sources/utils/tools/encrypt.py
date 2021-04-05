from pickle import dumps


def encrypt(obj) -> bytes:
    data = dumps(obj, 0)
    return data
