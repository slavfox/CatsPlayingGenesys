# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Base datatypes for cat activities."""
from typing import TYPE_CHECKING, Dict, List, Optional, Type
from abc import ABC, abstractmethod

import attr

from genesys_cats.genesys.datatypes import NPC, Location
from genesys_cats.util.discord import DiscordMessage

if TYPE_CHECKING:
    from genesys_cats.models import Cat


event_types: Dict[str, Type["Event"]] = {}
quest_types: Dict[str, Type["Quest"]] = {}


@attr.s(auto_attribs=True, slots=True, auto_detect=True)
class Event(ABC):
    """An ongoing Event."""

    def __init_subclass__(cls, **_):
        event_types[cls.__name__] = cls

    @abstractmethod
    def generate_update(
        self, state: "GameState", cats: List["Cat"]
    ) -> DiscordMessage:
        """Generate a new happening, potentially ending this Event."""
        ...


@attr.s(auto_attribs=True, slots=True, auto_detect=True)
class Quest(ABC):
    """A Quest the party has been tasked with."""

    encounters_left: int
    destination: Location

    def __init_subclass__(cls, **_):
        quest_types[cls.__name__] = cls


@attr.s(auto_attribs=True, slots=True, auto_detect=True)
class GameState:
    """Main game state representation."""

    current_event: Event
    quests: List[Quest] = attr.ib(factory=list)
    known_locations: List[Location] = attr.ib(factory=list)
    nemeses: List[NPC] = attr.ib(factory=list)

    @property
    def current_quest(self) -> Optional[Quest]:
        """Return the current top quest."""
        if self.quests:
            return self.quests[-1]
        return None
