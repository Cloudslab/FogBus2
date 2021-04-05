from typing import Tuple

from dotenv import dotenv_values

from .base import Config

environment = dotenv_values(".env")

portRangeStr = environment['TASK_EXECUTOR_PORT_RANGE']
portRange = portRangeStr.split('-')


class ConfigTaskExecutor(Config):
    portRange: Tuple[int, int] = (int(portRange[0]), int(portRange[1]) + 1)
