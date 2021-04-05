from typing import Set
from typing import Union

from ..base import BaseScheduler
from ..policies.nsga.nsga2 import NSGA2
from ..policies.nsga.nsga3 import NSGA3
from ..policies.nsga.ohnsga import OHNSGA
from ....component.basic import BasicComponent
from ....types import Address


def initSchedulerByName(
        knownMasters: Set[Address],
        minimumActors: int,
        schedulerName: str,
        basicComponent: BasicComponent,
        isContainerMode: bool,
        parsedArgs,
        **kwargs) -> Union[BaseScheduler, None]:
    if schedulerName == 'OHNSGA':
        populationSize = kwargs['populationSize']
        generationNum = kwargs['generationNum']
        estimationThreadNum = 4
        if parsedArgs is not None and 'estimationThreadNum' in parsedArgs:
            estimationThreadNum = parsedArgs.estimationThreadNum
        scheduler = OHNSGA(
            knownMasters=knownMasters,
            minimumActors=minimumActors,
            populationSize=populationSize,
            generationNum=generationNum,
            basicComponent=basicComponent,
            estimationThreadNum=estimationThreadNum,
            isContainerMode=isContainerMode)
        return scheduler
    elif schedulerName == 'NSGA2':
        populationSize = kwargs['populationSize']
        generationNum = kwargs['generationNum']
        estimationThreadNum = 4
        if parsedArgs is not None and 'estimationThreadNum' in parsedArgs:
            estimationThreadNum = parsedArgs.estimationThreadNum
        scheduler = NSGA2(
            knownMasters=knownMasters,
            minimumActors=minimumActors,
            populationSize=populationSize,
            generationNum=generationNum,
            basicComponent=basicComponent,
            estimationThreadNum=estimationThreadNum,
            isContainerMode=isContainerMode)
        return scheduler
    elif schedulerName == 'NSGA3':
        populationSize = kwargs['populationSize']
        generationNum = kwargs['generationNum']
        estimationThreadNum = 4
        if parsedArgs is not None and 'estimationThreadNum' in parsedArgs:
            estimationThreadNum = parsedArgs.estimationThreadNum
        scheduler = NSGA3(
            knownMasters=knownMasters,
            minimumActors=minimumActors,
            populationSize=populationSize,
            generationNum=generationNum,
            basicComponent=basicComponent,
            estimationThreadNum=estimationThreadNum,
            isContainerMode=isContainerMode)
        return scheduler
    elif schedulerName == 'Random':
        from ..policies.schedulerRandomPolicy import \
            SchedulerRandomPolicy
        scheduler = SchedulerRandomPolicy(isContainerMode=isContainerMode)
        return scheduler
    elif schedulerName == 'RoundRobin':
        from ..policies.schedulerRoundRobinPolicy import \
            SchedulerRoundRobinPolicy
        scheduler = SchedulerRoundRobinPolicy(isContainerMode=isContainerMode)
        return scheduler
    return None
