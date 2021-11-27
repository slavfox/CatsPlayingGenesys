# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Common RPG utilities and data."""
import random
from typing import TYPE_CHECKING, List, Union

from genesys_cats.util.cats import GenesysStat, PersonalityStat
from genesys_cats.util.rng import random_order

if TYPE_CHECKING:
    from genesys_cats.models import Cat


# Valley of X
TITLES = [
    "Dragons",
    "Vampires",
    "the Two Kings",
    "Death",
    "Silence",
    "Fire",
    "Water",
    "Air",
    "Earth",
    "Peace",
]

GENERIC_INTERACTIONS = [
    "meets",
    "chats with",
    "exchanges rumours with",
    "barters with",
    "passes",
    "notices",
    "gets in a minor argument with",
    "gets directions from",
]


def get_participating_cats(
    cats: List["Cat"],
    attr: Union[PersonalityStat, GenesysStat],
    negative: bool = False,
) -> List["Cat"]:
    """
    Return a list of cats participating in an event, with the chance of
    participation based on a personality stat.
    """
    participating_cats = []

    for cat in random_order(cats):
        base_roll = 100
        base_attr = getattr(cat, attr.value)
        spontaneity_offset = cat.spontaneity * random.uniform(-1, 1)
        target = (base_roll + base_attr + spontaneity_offset) / 300
        if negative:
            target = 1.0 - target
        if random.random() < target:
            participating_cats.append(cat)

    if len(participating_cats) == len(cats):
        return []

    return participating_cats
