from time import time

from pymoo.util.termination.default import SingleObjectiveDefaultTermination


class TimeBasedSingleObjectiveDefaultTermination(
    SingleObjectiveDefaultTermination):

    def __init__(self, maxTime=1e-5, **kwargs):
        SingleObjectiveDefaultTermination.__init__(self, **kwargs)
        self.do_continueTemp = SingleObjectiveDefaultTermination.do_continue
        self.maxTime = maxTime
        self.startTime = time()

    def do_continue(self, algorithm):
        if time() - self.startTime > self.maxTime:
            return False
        self.do_continueTemp(self, algorithm)
