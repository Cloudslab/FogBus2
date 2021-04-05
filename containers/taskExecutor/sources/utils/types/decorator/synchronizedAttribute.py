from collections import defaultdict
from threading import Lock
from typing import DefaultDict


class SynchronizedAttribute:
    locks: DefaultDict[str, Lock] = defaultdict(lambda: Lock())

    def __init__(self, f):
        self.f = f

    def __call__(self, *args, **kwargs):
        self.locks[kwargs['attributeName']].acquire()
        # print('[+] ', kwargs['attributeName'])
        ret = self.f(*args, **kwargs)
        self.locks[kwargs['attributeName']].release()
        # print('[-] ', kwargs['attributeName'])
        return ret
