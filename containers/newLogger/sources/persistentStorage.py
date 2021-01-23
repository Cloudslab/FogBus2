import json
import os
from typing import Dict
from copy import deepcopy
from edge import Edge
from resourcesInfo import ResourcesInfo, WorkerInfo


class PersistentStorage:

    def __init__(
            self,
            toFile: bool = True,
            folder: str = 'profiler'):
        self.__toFile: bool = toFile
        self.__folder: str = folder

        if not os.path.exists(folder):
            os.mkdir(folder)

    def save(self, filename: str, _dict: Dict):
        _dictCopy = deepcopy(_dict)

        for key, value in _dictCopy.items():
            _dictCopy[key] = self.__covert(value)

        if self.__toFile:
            self.__saveDictToFileInJson(filename, _dictCopy)

    @staticmethod
    def __covert(obj):
        if isinstance(obj, Edge):
            return dict(obj)
        if isinstance(obj, ResourcesInfo):
            return dict(obj)
        if isinstance(obj, WorkerInfo):
            objDict = dict(obj)
            for k, v in objDict.items():
                objDict[k] = list(v)
            return objDict
        return obj

    def __saveDictToFileInJson(self, filename: str, content: Dict):
        with open(
                os.path.join(self.__folder, filename),
                'w') as outfile:
            json.dump(content, outfile)
