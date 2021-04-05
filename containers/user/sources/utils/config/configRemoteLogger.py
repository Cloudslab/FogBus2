from typing import Tuple

from dotenv import dotenv_values

from .base import Config

environment = dotenv_values(".env")

portRangeStr = environment['REMOTE_LOGGER_PORT_RANGE']
portRange = portRangeStr.split('-')


class ConfigRemoteLogger(Config):
    portRange: Tuple[int, int] = (int(portRange[0]), int(portRange[1]) + 1)
