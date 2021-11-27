# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""RNG related utilities."""
import random
from typing import List, Sequence, TypeVar

T = TypeVar("T")


def select_weighted(
    haystack: Sequence[T], weights: Sequence[float], k: int = 1
) -> List[T]:
    """
    Select ``k`` unique elements from ``haystack``, weighted by ``weights``.

    Weighted version of random.select.
    """
    weights_: "List[float]" = list(weights)
    idxs: "List[int]" = list(range(len(haystack)))
    results: "List[T]" = []
    needed = k - len(results)
    while needed:
        for i in random.choices(idxs, weights_, k=needed):
            if weights_[i]:
                weights_[i] = 0.0
                results.append(haystack[i])
                needed -= 1
        needed = k - len(results)
    return results


def random_order(xs: List[T]) -> List[T]:
    """Return `xs` in a random order."""
    return random.sample(xs, len(xs))


# Weights for rounded integers [0, 100] generated from a normal
# distribution with mean = 50 and dev = 20, then normalized to 0..1.
#
# In Sheets, this is
# ```text
# 1 | A | B                            | C
# ---------------------------------------------------
# 2 | 0 | =NORM.DIST(A2, 50, 20, True) | =B2/MAX(B:B)
# 3 | 1 | ...                          | ...
# 4 | 2 | ...                          | ...
# ```
WEIGHTS = [
    0.00624846621,
    0.007187442347,
    0.008248757951,
    0.009445358047,
    0.01079111926,
    0.01230085686,
    0.01399032274,
    0.01587619324,
    0.01797604579,
    0.0203083233,
    0.02289228538,
    0.02574794565,
    0.02889599427,
    0.03235770532,
    0.0361548285,
    0.04030946515,
    0.04484392855,
    0.04978058883,
    0.05514170322,
    0.06094923234,
    0.06722464381,
    0.0739887047,
    0.08126126449,
    0.08906103063,
    0.09740533914,
    0.1063099227,
    0.1157886792,
    0.1258534434,
    0.1365137657,
    0.1477767002,
    0.1596466059,
    0.1721249647,
    0.1852102188,
    0.1988976308,
    0.2131791699,
    0.2280434257,
    0.2434755539,
    0.2594572535,
    0.2759667791,
    0.2929789883,
    0.3104654251,
    0.3283944399,
    0.346731344,
    0.3654386002,
    0.3844760454,
    0.4038011443,
    0.423369272,
    0.4431340216,
    0.4630475329,
    0.4830608403,
    0.5031242331,
    0.5231876259,
    0.5432009333,
    0.5631144446,
    0.5828791942,
    0.6024473219,
    0.6217724208,
    0.640809866,
    0.6595171222,
    0.6778540264,
    0.6957830411,
    0.713269478,
    0.7302816871,
    0.7467912127,
    0.7627729123,
    0.7782050405,
    0.7930692963,
    0.8073508354,
    0.8210382474,
    0.8341235015,
    0.8466018603,
    0.858471766,
    0.8697347005,
    0.8803950228,
    0.890459787,
    0.8999385435,
    0.9088431271,
    0.9171874356,
    0.9249872017,
    0.9322597615,
    0.9390238224,
    0.9452992339,
    0.951106763,
    0.9564678774,
    0.9614045377,
    0.9659390011,
    0.9700936377,
    0.9738907609,
    0.9773524719,
    0.9805005206,
    0.9833561808,
    0.9859401429,
    0.9882724204,
    0.990372273,
    0.9922581435,
    0.9939476094,
    0.9954573469,
    0.9968031082,
    0.9979997083,
    0.9990610239,
    1.0,
]


def normal_integer_0_100() -> int:
    """An integer in the range [0, 100] following a normal distribution."""
    return random.choices(list(range(len(WEIGHTS))), cum_weights=WEIGHTS)[0]


def fixed_int(seed: str, min_: int, max_: int) -> int:
    """Return an integer based on a seed."""
    return random.Random(seed).randint(min_, max_)
