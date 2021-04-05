from typing import Tuple

from dotenv import dotenv_values

from .base import Config

environment = dotenv_values(".env")

portRangeStr = environment['ACTOR_PORT_RANGE']
portRange = portRangeStr.split('-')


class ConfigActor(Config):
    portRange: Tuple[int, int] = (int(portRange[0]), int(portRange[1]))
