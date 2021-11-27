# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""NPC-related lists and functions."""
import random
from typing import List, Optional, Tuple

import attr

from genesys_cats.genesys.datatypes import NPC
from genesys_cats.models import Cat

UNIVERSAL_NPCS = [
    NPC("cat"),
    NPC("dog"),
    NPC("smuggler"),
    NPC("merchant"),
    NPC("catnip dealer"),
]

TRAVELLING_NPCS = UNIVERSAL_NPCS + [
    NPC("traveller"),
    NPC("wanderer"),
    NPC("hermit"),
    NPC("explorer"),
]

VILLAGE_NPCS = UNIVERSAL_NPCS + [
    NPC("farmer"),
    NPC("peasant"),
    NPC("hunter"),
]

CITY_NPCS = UNIVERSAL_NPCS + [
    NPC("noblecat"),
    NPC("policecat"),
    NPC("guardscat"),
]

WOODS_NPCS = UNIVERSAL_NPCS + [
    NPC("druid"),
    NPC("wizard"),
    NPC("cultist"),
    NPC("elfcat"),
    NPC("witch"),
    NPC("hunter"),
    NPC("hermit"),
]

CAVE_NPCS = [
    NPC("dwarfcat"),
    NPC("hermit"),
    NPC("archaeologist"),
    NPC("explorer"),
]

MINE_NPCS = [
    NPC("miner"),
    NPC("dwarfcat"),
    NPC("worker"),
    NPC("union cat"),
]

PLACE_OF_POWER_NPCS = [
    NPC("wizard"),
    NPC("catnipmancer"),
    NPC("sorcerer"),
    NPC("witch"),
    NPC("alchemist"),
    NPC("warlock"),
    NPC("archaeologist"),
    NPC("explorer"),
]


@attr.s(auto_attribs=True, slots=True, auto_detect=True)
class CombatTemplate:
    """The template for a combat encounter."""

    message: str
    # List of enemies and the weights with which they appear.
    enemies: List[Tuple[NPC, int]]
    forced_enemies: Optional[List[NPC]] = None
    enemies_ambushed: bool = False
    cats_ambushed: bool = True

    def get_enemies(self, cats: List[Cat]) -> List[NPC]:
        """Get a list of enemies for the encounter."""
        hp_target = random.randint(len(cats) * 3, len(cats) * 10)

        if self.forced_enemies:
            # False positive
            # pylint: disable=not-an-iterable
            enemies = [attr.evolve(en) for en in self.forced_enemies]
        else:
            enemies = []

        total_enemy_hp = sum(en.hp for en in enemies)
        enemy_types, weights = zip(*self.enemies)

        while total_enemy_hp < hp_target:
            enemy: NPC = random.choices(enemy_types, weights=weights, k=1)[0]
            enemies.append(attr.evolve(enemy))
            total_enemy_hp += enemy.hp

        return enemies


BANDIT = NPC(
    "bandit",
    attack_attr=3,
    attack_skill=1,
    soak=4,
    hp=5,
    weapon="sword",
    weapon_damage=5,
    willpower=2,
    presence=1,
    defense=0,
)

BANDIT_LEADER = NPC(
    "bandit leader",
    attack_attr=3,
    attack_skill=2,
    soak=4,
    hp=14,
    weapon="cutlass",
    weapon_damage=6,
    willpower=3,
    presence=3,
    defense=1,
)


BANDIT_AMBUSH = CombatTemplate(
    "gets ambushed by a group of bandits!",
    [(BANDIT, 5), (BANDIT_LEADER, 1)],
)

VAMPIRE = NPC(
    "vampire cat",
    attack_attr=4,
    attack_skill=3,
    weapon="vampiric bite",
    weapon_damage=5,
    willpower=4,
    presence=6,
    soak=4,
    hp=18,
    defense=2,
)

GHOUL = NPC(
    "ghoul",
    attack_attr=1,
    attack_skill=0,
    weapon="ghoulish swipe",
    weapon_damage=0,
    willpower=3,
    presence=3,
    soak=2,
    hp=5,
    defense=0,
)

VAMPIRE_ENCOUNTER = CombatTemplate(
    "runs into a vampire feeding on a dead villager! It's a fight!",
    [(GHOUL, 1)],
    forced_enemies=[VAMPIRE],
    enemies_ambushed=True,
    cats_ambushed=True,
)

VAMPIRE_AMBUSH = CombatTemplate(
    "gets jumped by a vampire hoping for an easy meal!",
    [(GHOUL, 1)],
    forced_enemies=[VAMPIRE],
    enemies_ambushed=True,
    cats_ambushed=True,
)

SPIDER_BOSS = NPC(
    "giant spidercat queen",
    attack_attr=6,
    attack_skill=2,
    weapon="enormous fangs",
    weapon_damage=7,
    willpower=3,
    presence=3,
    soak=8,
    hp=26,
    defense=1,
)


GIANT_SPIDER = NPC(
    "giant spidercat",
    attack_attr=4,
    attack_skill=2,
    weapon="venomous bite",
    weapon_damage=4,
    willpower=2,
    presence=1,
    soak=5,
    hp=14,
    defense=0,
)

SPIDER = NPC(
    "spidercat",
    attack_attr=1,
    attack_skill=0,
    weapon="venomous bite",
    weapon_damage=2,
    willpower=2,
    presence=1,
    soak=3,
    hp=5,
    defense=0,
)

SPIDER_SWARM = CombatTemplate(
    "gets closed in on by a swarm of spidercats!",
    [(SPIDER, 1)],
    enemies_ambushed=False,
    cats_ambushed=False,
)


GIANT_SPIDER_FIGHT = CombatTemplate(
    "is attacked by a giant spidercat!",
    [(SPIDER, 10), (GIANT_SPIDER, 1)],
    forced_enemies=[GIANT_SPIDER],
    enemies_ambushed=False,
    cats_ambushed=True,
)


SPIDER_QUEEN_FIGHT = CombatTemplate(
    "has angered the spidercat queen! It's a fight!",
    [(SPIDER, 10), (GIANT_SPIDER, 1)],
    forced_enemies=[SPIDER_BOSS],
    enemies_ambushed=False,
    cats_ambushed=False,
)


GUARDSCAT = NPC(
    "guardscat",
    attack_attr=3,
    attack_skill=1,
    soak=3,
    hp=7,
    weapon="truncheon",
    weapon_damage=5,
    willpower=2,
    presence=2,
    defense=1,
)


GUARD_CAPTAIN = NPC(
    "guard catptain",
    attack_attr=3,
    attack_skill=2,
    soak=4,
    hp=13,
    weapon="halberd",
    weapon_damage=7,
    willpower=2,
    presence=3,
    defense=1,
)


GUARD_FIGHT = CombatTemplate(
    "gets in a scuffle with some guards!",
    [(GUARDSCAT, 5), (GUARD_CAPTAIN, 1)],
    enemies_ambushed=False,
    cats_ambushed=False,
)

DOGCAT = NPC(
    "wild dogcat",
    attack_attr=2,
    attack_skill=0,
    soak=2,
    hp=5,
    weapon="vicious bite",
    weapon_damage=4,
    willpower=1,
    presence=1,
    defense=0,
)

WILD_DOGCATS = CombatTemplate(
    "runs into a pack of angry wild dogcats!",
    [(DOGCAT, 1)],
    enemies_ambushed=False,
    cats_ambushed=False,
)

ORC = NPC(
    "orc cat warrior",
    attack_attr=4,
    attack_skill=1,
    soak=4,
    hp=12,
    weapon="axe",
    weapon_damage=8,
    willpower=1,
    presence=1,
    defense=0,
)


ORCS_FIGHT = CombatTemplate(
    "gets attacked by a gang of orc cats!",
    [(ORC, 1)],
    enemies_ambushed=False,
    cats_ambushed=False,
)
