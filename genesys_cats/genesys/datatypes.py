# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Common data types for the RPG module."""
from typing import List, Optional
from enum import Enum

import attr

from genesys_cats.util.rng import fixed_int
from genesys_cats.util.text import capfirst, p


class LocationType(Enum):
    """
    The type of a location; determines what events the cats may encounter.
    """

    EN_ROUTE = 0
    CITY = 1
    VILLAGE = 2
    WOODS = 3
    CAVE = 4
    MINE = 5
    PLACE_OF_POWER = 6


@attr.s(auto_attribs=True, slots=True, auto_detect=True)
class Location:
    """A location in the game world."""

    article: Optional[str]
    name: str
    short_name: str
    location_type: LocationType
    known_npcs: List["NPC"] = attr.ib(factory=list)

    def __str__(self) -> str:
        if self.article:
            return f"{self.article} {self.name}"
        return self.name


@attr.s(auto_attribs=True, slots=True, auto_detect=True)
class NPC:
    """An NPC."""

    name: str
    generic: bool = True
    attack_attr: int = 2
    attack_skill: int = 0
    presence: int = 2
    willpower: int = 2
    soak: int = 2
    hp: int = 10
    weapon: str = "fists"
    weapon_damage: int = 3
    defense: int = 1

    def __str__(self) -> str:
        if self.generic:
            return f"{p.a(self.name)}"
        return self.name

    @property
    def capname(self) -> str:
        """This NPC's name, with the first letter capitalized."""
        return capfirst(str(self))

    def get_skill_value(self, skill: str) -> int:
        """Get the value for a skill."""
        if self.generic:
            return fixed_int(f"{self.name}_{skill}", min_=0, max_=2)
        return fixed_int(f"{self.name}_{skill}", min_=0, max_=3)
