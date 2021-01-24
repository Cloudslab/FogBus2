from pymoo.algorithms.nsga3 import NSGA3 as NSGA3_
from pymoo.factory import get_problem, get_reference_directions
from pymoo.optimize import minimize
from pymoo.visualization.scatter import Scatter
from persistentStorage import PersistentStorage
from abc import abstractmethod
from pymoo.model.problem import Problem


class SchedulingMethod:

    @abstractmethod
    def schedule(self):
        pass


class NSGA3Problem(Problem):

    def __init__(self):
        super().__init__()

    def _evaluate(self, x, out, *args, **kwargs):
        pass


class NSGA3(SchedulingMethod):
    def __init__(self):
        self.__refDirs = get_reference_directions("das-dennis", 3, n_partitions=12)
        self.__algorithm = NSGA3_(pop_size=92, ref_dirs=self.__refDirs)
        self.__problem = NSGA3Problem()
        res = minimize(self.__problem,
                       self.__algorithm,
                       seed=1,
                       termination=('n_gen', 600))

    def schedule(self):
        pass

    def __defineProblem(self) -> Problem:
        pass


if __name__ == '__main__':
    pass
