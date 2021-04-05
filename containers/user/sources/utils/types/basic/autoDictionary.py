class AutoDictionary:

    def _dict(self):
        publicItems = {}

        for key, value in self.__dict__.items():
            if '_' == key[0]:
                continue
            publicItems[key] = value
        return publicItems

    def __repr__(self):
        return self._dict().__repr__()

    def __iter__(self):
        for k, v in self._dict().items():
            yield k, v
