from time import time
from pprint import pformat
from .base import ApplicationUserSide
from ...component.basic import BasicComponent


class NaiveFormulaParallelized(ApplicationUserSide):

    def __init__(
            self,
            videoPath: str,
            targetHeight: int,
            showWindow: bool,
            basicComponent: BasicComponent):
        super().__init__(
            appName='NaiveFormulaParallelized',
            videoPath=videoPath,
            targetHeight=targetHeight,
            showWindow=showWindow,
            basicComponent=basicComponent)

    def prepare(self):
        pass

    def _run(self):
        self.basicComponent.debugLogger.info(
            'Application is running: %s', self.appName)

        # get user input of a, b, and c
        print('a = ', end='')
        a = int(input())
        print('b = ', end='')
        b = int(input())
        print('c = ', end='')
        c = int(input())

        inputData = {
            'a': a,
            'b': b,
            'c': c
        }

        # put it in to data uploading queue
        self.dataToSubmit.put(inputData)
        lastDataSentTime = time()
        self.basicComponent.debugLogger.info(
            'Data has sent (a, b, c): %.2f, %.2f, %.2f', a, b, c)

        # wait for all the 4 results
        while True:
            result = self.resultForActuator.get()

            responseTime = (time() - lastDataSentTime) * 1000
            self.responseTime.update(responseTime)
            self.responseTimeCount += 1

            if 'finalResult' in result:
                break

        for key, value in result.items():
            result[key] = '%.4f' % value
        self.basicComponent.debugLogger.info(
            'Received all the 4 results: \r\n%s', pformat(result))
