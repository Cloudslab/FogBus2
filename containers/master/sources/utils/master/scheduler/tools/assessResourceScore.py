from ....types import Resources


def assessResourceScore(resources: Resources) -> float:
    score = (1 - resources.cpu.utilization) * resources.cpu.cores \
            * resources.cpu.frequency
    return score
