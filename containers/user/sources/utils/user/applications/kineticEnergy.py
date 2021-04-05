from time import time

from .base import ApplicationUserSide
from ...component.basic import BasicComponent


class KineticEnergy(ApplicationUserSide):

    def __init__(
            self,
            videoPath: str,
            targetHeight: int,
            showWindow: bool,
            basicComponent: BasicComponent):
        super().__init__(
            appName='KineticEnergy',
            videoPath=videoPath,
            targetHeight=targetHeight,
            showWindow=showWindow,
            basicComponent=basicComponent)

    def prepare(self):
        pass

    def _run(self):
        self.basicComponent.debugLogger.info(
            'Application is running: %s', self.appName)

        m, v0, v1 = 4.2, 10., 12.
        inputData = {
            'm': m,
            'v0': v0,
            'v1': v1
        }
        self.dataToSubmit.put(inputData)
        lastDataSentTime = time()
        self.basicComponent.debugLogger.info(
            'Data has sent (m, v0, v1): %f.2, %f.2, %f.2', m, v0, v1)

        result = self.resultForActuator.get()
        responseTime = (time() - lastDataSentTime) * 1000
        self.responseTime.update(responseTime)
        self.responseTimeCount += 1

        self.basicComponent.debugLogger.info('The result is: %f.2', result)
