import pickle
import struct


class Message:

    @staticmethod
    def encrypt(obj):
        data = pickle.dumps(obj, 0)
        return data

    @staticmethod
    def decrypt(msg):
        obj = pickle.loads(msg, fix_imports=True, encoding="bytes")
        return obj
