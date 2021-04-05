from .sequenceMedian import SequenceMedian


class PairsMedian(dict):

    def __missing__(self, key):
        self.__setitem__(key, SequenceMedian())
        return self.__getitem__(key)

    def calculateAll(self):
        items = self.items()
        logFormat = {}
        for key, sequence in items:
            logFormat[key] = sequence.median()
        return logFormat
