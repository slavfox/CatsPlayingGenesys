# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Downtime events; ie. anything without any action."""
import random
from typing import TYPE_CHECKING, Callable, List, Optional
from logging import getLogger

import attr

from genesys_cats.config import config
from genesys_cats.genesys.core import Event, GameState
from genesys_cats.genesys.datatypes import NPC, Location, LocationType
from genesys_cats.genesys.gm.combat import Combat
from genesys_cats.genesys.gm.common import (
    GENERIC_INTERACTIONS,
    get_participating_cats,
)
from genesys_cats.genesys.gm.npcs import (
    BANDIT_AMBUSH,
    CAVE_NPCS,
    CITY_NPCS,
    GIANT_SPIDER_FIGHT,
    GUARD_FIGHT,
    MINE_NPCS,
    ORCS_FIGHT,
    PLACE_OF_POWER_NPCS,
    SPIDER_QUEEN_FIGHT,
    SPIDER_SWARM,
    TRAVELLING_NPCS,
    VAMPIRE_AMBUSH,
    VAMPIRE_ENCOUNTER,
    VILLAGE_NPCS,
    WILD_DOGCATS,
    WOODS_NPCS,
    CombatTemplate,
)
from genesys_cats.util.cats import GenesysStat, PersonalityStat
from genesys_cats.util.discord import DiscordMessage
from genesys_cats.util.image import combine_images
from genesys_cats.util.text import describe_cats_list, p

if TYPE_CHECKING:
    from genesys_cats.models import Cat

TRAVEL_VERBS = [
    "reaches",
    "finds",
    "arrives at",
    "comes to",
    "stumbles upon",
    "approaches",
    "is travelling through",
    "passes through",
    "discovers",
    "journeys through",
    "visits",
    "stops at",
]

GETTING_LOST_VERBS = [
    "gets lost",
    "wanders off",
    "loses the way",
    "stumbles aimlessly",
]

GENERIC_LOCATIONS = [
    # En route
    Location("a", "barren desert", "desert", LocationType.EN_ROUTE),
    Location("a", "stormy coast", "coast", LocationType.EN_ROUTE),
    Location(
        "a",
        "picturesque mountain pass",
        "mountain pass",
        LocationType.EN_ROUTE,
    ),
    Location(
        "a",
        "forest path",
        "forest path",
        LocationType.EN_ROUTE,
    ),
    # Cities
    Location("a", "merchant district", "merchant district", LocationType.CITY),
    Location("a", "prosperous city", "city", LocationType.CITY),
    Location("a", "sprawling city", "city", LocationType.CITY),
    Location("an", "ancient city", "city", LocationType.CITY),
    Location("a", "majestic castle", "castle", LocationType.CITY),
    Location("a", "peaceful town", "town", LocationType.CITY),
    # Villages
    Location("a", "seaside village", "village", LocationType.VILLAGE),
    Location("a", "suspicious village", "village", LocationType.VILLAGE),
    Location("a", "peaceful village", "village", LocationType.VILLAGE),
    Location("a", "quiet village", "village", LocationType.VILLAGE),
    Location("a", "small settlement", "settlement", LocationType.VILLAGE),
    # Woods
    Location("a", "dense forest", "forest", LocationType.WOODS),
    Location(None, "mysterious woods", "woods", LocationType.WOODS),
    # Caves
    Location("a", "dark cave", "cave", LocationType.CAVE),
    Location("an", "ominous cave", "cave", LocationType.CAVE),
    Location("a", "sprawling cavern", "cavern", LocationType.CAVE),
    # Mines
    Location("a", "dwarven mine", "mine", LocationType.MINE),
    Location("an", "abandoned mineshaft", "mineshaft", LocationType.MINE),
    # Places of power
    Location("a", "mysterious ruin", "ruin", LocationType.PLACE_OF_POWER),
    Location("an", "ancient shrine", "shrine", LocationType.PLACE_OF_POWER),
]


def meet_generic_npc(
    npc_pool: List[NPC],
) -> Callable[["GameState", Location, List["Cat"]], DiscordMessage]:
    """Meet a random unnamed friendly NPC."""

    # pylint: disable=unused-argument
    def inner(
        state: "GameState", location: Location, cats: List["Cat"]
    ) -> DiscordMessage:
        participating_cats = get_participating_cats(
            cats, PersonalityStat.OUTGOINGNESS
        )
        if len(participating_cats) == len(cats):
            participating_cats = []
        npc = random.choice(npc_pool)
        interaction = random.choice(GENERIC_INTERACTIONS)
        if len(participating_cats) > 1:
            parts = interaction.split(maxsplit=1)
            interaction = " ".join([p.plural_verb(parts[0])] + parts[1:])
        return DiscordMessage(
            content=f"🗣️ {describe_cats_list(participating_cats)} "
            f"{interaction} "
            f"{npc} at the {location.short_name}. 🗣️",
            image=combine_images([cat.image for cat in participating_cats]),
        )

    return inner


# pylint: disable=unused-argument
def get_lost(state: "GameState", location: Location, cats: List["Cat"]):
    """The party gets lost."""
    participating_cats = get_participating_cats(
        cats, PersonalityStat.SPONTANEITY
    )
    if len(participating_cats) == len(cats):
        participating_cats = []
    description = random.choice(GETTING_LOST_VERBS)
    if len(participating_cats) > 1:
        parts = description.split(maxsplit=1)
        description = " ".join([p.plural_verb(parts[0])] + parts[1:])
    return DiscordMessage(
        content=f"🧭 {describe_cats_list(participating_cats)} "
        f"{description} "
        f"in the {location.short_name}. 🧭",
        image=combine_images([cat.image for cat in participating_cats]),
    )


FINDS_VERBS = [
    "finds",
    "stumbles upon",
    "discovers",
    "notices",
    "comes across",
    "spots",
]


def find_thing(
    things: List[str],
) -> Callable[["GameState", Location, List["Cat"]], DiscordMessage]:
    """Find a thing."""

    # pylint: disable=unused-argument
    def inner(
        state: "GameState", location: Location, cats: List["Cat"]
    ) -> DiscordMessage:
        participating_cats = get_participating_cats(
            cats, GenesysStat.PLAYFULNESS
        )

        if len(participating_cats) == len(cats):
            participating_cats = []

        thing = random.choice(things)
        interaction = random.choice(FINDS_VERBS)

        if len(participating_cats) > 1:
            parts = interaction.split(maxsplit=1)
            interaction = " ".join([p.plural_verb(parts[0])] + parts[1:])

        return DiscordMessage(
            content=f"🔍 {describe_cats_list(participating_cats)} "
            f"{interaction} "
            f"{thing}. 🔍",
            image=combine_images([cat.image for cat in participating_cats]),
        )

    return inner


def combat_encounter(
    encounters: List[CombatTemplate],
) -> Callable[["GameState", Location, List["Cat"]], DiscordMessage]:
    """Get in combat."""
    # pylint: disable=unused-argument
    def inner(
        state: "GameState", location: Location, cats: List["Cat"]
    ) -> DiscordMessage:
        participating_cats = get_participating_cats(
            cats, GenesysStat.PLAYFULNESS
        )

        if len(participating_cats) == len(cats):
            participating_cats = []

        encounter = random.choice(encounters)

        if len(participating_cats) > 1:
            parts = encounter.message.split(maxsplit=1)
            message = " ".join([p.plural_verb(parts[0])] + parts[1:])
        else:
            message = encounter.message

        return attr.evolve(
            Combat.start(
                state,
                cats,
                state.current_event,
                encounter.get_enemies(cats),
                cats_ambushed=encounter.cats_ambushed,
                enemies_ambushed=encounter.enemies_ambushed,
            ),
            content=f"🤼 {describe_cats_list(participating_cats)} "
            f"{message} 🤼",
            image=combine_images([cat.image for cat in participating_cats]),
        )

    return inner


LOCATION_TYPE_EVENTS = {
    LocationType.EN_ROUTE: [
        meet_generic_npc(TRAVELLING_NPCS),
        combat_encounter([BANDIT_AMBUSH, WILD_DOGCATS] * 2 + [ORCS_FIGHT]),
    ],
    LocationType.CITY: [
        meet_generic_npc(CITY_NPCS),
    ]
    * 3
    + [
        combat_encounter([BANDIT_AMBUSH, GUARD_FIGHT]),
    ],
    LocationType.VILLAGE: [
        meet_generic_npc(VILLAGE_NPCS),
    ]
    * 3
    + [
        combat_encounter([VAMPIRE_ENCOUNTER, BANDIT_AMBUSH, BANDIT_AMBUSH]),
    ],
    LocationType.WOODS: [
        meet_generic_npc(WOODS_NPCS),
        get_lost,
        combat_encounter(
            [VAMPIRE_AMBUSH, WILD_DOGCATS, WILD_DOGCATS, ORCS_FIGHT]
        ),
        find_thing(
            [
                "a grouping of trees with deep rut marks",
                "the husk of an ancient tree, struck down by lightning",
                "a dense thicket, blocking all natural light",
                "a small, peaceful clearing",
                "a resting bear, watching the party from a distance",
            ]
        ),
    ],
    LocationType.CAVE: [
        meet_generic_npc(CAVE_NPCS),
        get_lost,
        find_thing(
            [
                "a pile of spider egg shells",
                "a collapsed tunnel",
                "the skeleton of an unfamiliar beast",
                "a faded map scratched into the cave wall",
                "a broken lantern buried in rocks",
                "an immense cavern, stretching out further than light can "
                "reach",
                "a fathomless underground chasm",
                "ancient charcoal paintings of scenes from before history",
                "a small pool with stalactites dripping overhead",
            ]
        ),
        combat_encounter(
            [
                SPIDER_SWARM,
                SPIDER_SWARM,
                SPIDER_SWARM,
                GIANT_SPIDER_FIGHT,
                GIANT_SPIDER_FIGHT,
                SPIDER_QUEEN_FIGHT,
            ]
        ),
    ],
    LocationType.MINE: [
        meet_generic_npc(MINE_NPCS),
        get_lost,
        find_thing(
            [
                "a shining diamond",
                "the skeleton of a long-dead miner, buried by rockfall",
                "a gold vein",
                "a half-collapsed old mineshaft",
                "an unexploded stick of dynamite, missing its fuse",
                "a broken pickaxe, its surface marred by deep claw marks",
                "a skull, half-embedded in the wall of the mineshaft",
            ]
        ),
    ],
    LocationType.PLACE_OF_POWER: [
        meet_generic_npc(PLACE_OF_POWER_NPCS),
        find_thing(
            [
                "some ancient carvings",
                "a mysterious orb, humming with power",
                "a patch of rare herbs",
                "a spellbook, burnt beyond use",
                "a burnt gash on a wall, whispering with the "
                "echoes of a magical duel from centuries ago",
                "a circle on the ground where no sound can be heard",
                "two tree trunks that join into a single crown",
                "a water fountain flowing in reverse",
                "an obsidian obelisk, silently beckoning",
            ]
        ),
    ],
}

assert all(len(LOCATION_TYPE_EVENTS[lt]) > 0 for lt in LocationType)


def generate_location_event(
    state: "GameState", location: Location, cats: List["Cat"]
) -> DiscordMessage:
    """Generate a non-quest event for a given location."""
    events = LOCATION_TYPE_EVENTS[location.location_type]
    # TODO
    # if location.known_npcs:
    #     events = events + [meet_friend]
    make_event = random.choice(events)
    return make_event(state, location, cats)


logger = getLogger("travel")


@attr.s(auto_attribs=True, slots=True, auto_detect=True)
class Travel(Event):
    """The cats are travelling."""

    current_location: Optional[Location] = None
    destination: Optional[Location] = None

    @classmethod
    def start(
        cls,
        state: GameState,
    ) -> DiscordMessage:
        """Start travel."""
        logger.info("Party starts travelling.")
        current_quest = state.current_quest
        if current_quest:
            destination: Optional[Location] = current_quest.destination
        else:
            destination = None

        state.current_event = Travel(
            destination=destination, current_location=None
        )

        if destination:
            return DiscordMessage(
                content=f"🗺️ The party sets off towards {destination}. 🗺️"
            )
        return DiscordMessage(content="🗺️ The party sets off. 🗺️")

    def generate_update(
        self, state: GameState, cats: List["Cat"]
    ) -> DiscordMessage:
        """Generate travel update."""
        logger.info("Party is traveling")
        if self.current_location:
            if random.random() < config.gm_travel_happening_chance:
                logger.info("Triggering location event")
                return self.generate_location_event(state, cats)
        logger.info("Travelling")
        reaches = random.choice(TRAVEL_VERBS)

        self.current_location = attr.evolve(
            random.choice(
                [
                    loc
                    for loc in GENERIC_LOCATIONS
                    if loc.name
                    != (
                        self.current_location.name
                        if self.current_location
                        else None
                    )
                ]
            )
        )
        return DiscordMessage(
            content=f"🏞 The party {reaches} {self.current_location}. 🏞"
        )

    def generate_location_event(
        self, state: GameState, cats: List["Cat"]
    ) -> DiscordMessage:
        """Generate a new event for a location."""
        assert self.current_location is not None
        current_quest = state.current_quest
        if current_quest is not None and current_quest.encounters_left > 0:
            if random.random() < config.gm_travel_quest_encounter_chance:
                pass
                # TODO
                # return do_quest_encounter()
        return generate_location_event(state, self.current_location, cats)
