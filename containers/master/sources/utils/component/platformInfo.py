import platform
from typing import Dict
from typing import List

from ..types.basic.serializableDictionary import SerializableDictionary


class PlatformInfo(SerializableDictionary):

    def __init__(
            self,
            architecture: List[str] = None,
            machine: str = None,
            node: str = None,
            platform_: str = None,
            release: str = None,
            processor: str = None,
            system: str = None,
            version: str = None,
            uname: List[str] = None,
            systemAlias: List[str] = None
    ):
        if architecture is None:
            self.architecture = list(platform.architecture())
        else:
            self.architecture = architecture
        if machine is None:

            self.machine = platform.machine()
        else:
            self.machine = machine
        if node is None:
            self.node = platform.node()
        else:
            self.node = node
        if platform_ is None:
            self.platform = platform.platform()
        else:
            self.platform = platform_
        if processor is None:

            self.processor = platform.processor()
        else:
            self.processor = processor
        if release is None:
            self.release = platform.release()
        else:
            self.release = release
        if system is None:
            self.system = platform.system()
        else:
            self.system = system
        if version is None:
            self.version = platform.version()
        else:
            self.version = version
        if uname is None:
            self.uname = list(platform.uname())
        else:
            self.uname = uname
        if systemAlias is None:
            self.systemAlias = list(platform.system_alias(
                system=self.system,
                release=self.release,
                version=self.version
            ))
        else:
            self.systemAlias = systemAlias

    def toDict(self):
        inDict = {
            'architecture': self.architecture,
            'machine': self.machine,
            'node': self.node,
            'platform': self.platform,
            'processor': self.processor,
            'release': self.release,
            'system': self.system,
            'version': self.version,
            'uname': self.uname,
            'systemAlias': self.systemAlias
        }
        return inDict

    @staticmethod
    def fromDict(inDict: Dict):
        platform_ = PlatformInfo(
            architecture=inDict['architecture'],
            machine=inDict['machine'],
            node=inDict['node'],
            platform_=inDict['platform'],
            processor=inDict['processor'],
            release=inDict['release'],
            system=inDict['system'],
            version=inDict['version'],
            uname=inDict['uname'],
            systemAlias=inDict['systemAlias']
        )
        return platform_


if __name__ == '__main__':
    p = PlatformInfo()
    print()
