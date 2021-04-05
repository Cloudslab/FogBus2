# from: https://github.com/msu-coinlab/pymoo/-
# blob/b91212185ab04d006741372a4a480608b8d32e68/-
# pymoo/operators/selection
# /tournament_selection.py

import math

import numpy as np
from pymoo.model.selection import Selection
from pymoo.operators.selection.tournament_selection import compare
from pymoo.util.misc import random_permuations


class TournamentSelection(Selection):
    def __init__(self, func_comp=None, pressure=2):
        super().__init__()
        self.pressure = pressure

        self.f_comp = func_comp
        if self.f_comp is None:
            self.f_comp = self.compare

    def _do(self, pop, n_select, n_parents=1, **kwargs):
        n_random = n_select * n_parents * self.pressure
        n_perms = math.ceil(n_random / len(pop))
        P = random_permuations(n_perms, len(pop))[:n_random]
        P = np.reshape(P, (n_select * n_parents, self.pressure))
        S = self.f_comp(pop, P, **kwargs)
        return np.reshape(S, (n_select, n_parents))

    @staticmethod
    def compare(pop, P, **kwargs):
        S = np.full(P.shape[0], np.nan)
        for i in range(P.shape[0]):
            a, b = P[i, 0], P[i, 1]
            if pop[a].CV > 0.0 or pop[b].CV > 0.0:
                S[i] = compare(a, pop[a].CV, b, pop[b].CV,
                               method='smaller_is_better',
                               return_random_if_equal=True)
                continue
            if pop[a].F > 0.0 or pop[b].F > 0.0:
                S[i] = compare(a, pop[a].F, b, pop[b].F,
                               method='smaller_is_better',
                               return_random_if_equal=True)
                continue
            S[i] = np.random.choice([a, b])

        return S[:, None].astype(np.int, copy=False)
