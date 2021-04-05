import numpy as np
from pymoo.operators.selection.tournament_selection import compare


def selectionCmp(pop, P, **kwargs):
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
