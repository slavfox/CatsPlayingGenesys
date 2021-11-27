# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Combat handling."""
import random
from typing import Dict, List, Set, Tuple, Union
from logging import getLogger

import attr
from discord import Colour, Embed

from genesys_cats.bot.helpers import BOT_EMBED_COLOUR
from genesys_cats.genesys.core import Event, GameState
from genesys_cats.genesys.datatypes import NPC
from genesys_cats.genesys.gm.dice import (
    DicePool,
    DiceResult,
    get_cat_dice_pool,
    grant_random_bonus_dice,
)
from genesys_cats.models import Cat
from genesys_cats.util.cats import GenesysStat
from genesys_cats.util.discord import DiscordMessage
from genesys_cats.util.rng import fixed_int, random_order
from genesys_cats.util.text import describe_npcs_list, p

logger = getLogger("combat")


@attr.s(auto_attribs=True, slots=True, auto_detect=True)
class RollModifiers:
    """Modifiers to be applied to the next roll."""

    boost: int = 0
    setback: int = 0
    upgrades: int = 0
    difficulty_upgrades: int = 0

    def apply_modifiers(
        self, dice_pool: DicePool
    ) -> Tuple[List[str], List[str]]:
        """Apply modifiers and return reasons for random bonuses, if any."""
        dice_pool.upgrade(self.upgrades).upgrade_difficulty(
            self.difficulty_upgrades
        )
        dice_pool.boost += self.boost
        dice_pool.setback += self.setback
        return grant_random_bonus_dice(dice_pool)


IsCatSlot = bool

CAT_ATTACK_SKILLS = [
    ("Archery", GenesysStat.ZOOMIES),
    ("Artillery", GenesysStat.ZOOMIES),
    ("Bap", GenesysStat.CHONK),
    ("Claws", GenesysStat.CHONK),
    ("Cuteness", GenesysStat.PURR_VOLUME),
    ("Hissing", GenesysStat.PURR_VOLUME),
    ("Loud Meowing", GenesysStat.PURR_VOLUME),
    ("Pouncing", GenesysStat.ZOOMIES),
    ("Ranged (Heavy)", GenesysStat.ZOOMIES),
    ("Ranged (Light)", GenesysStat.ZOOMIES),
    ("Slap", GenesysStat.CHONK),
    ("Swording", GenesysStat.CHONK),
]


@attr.s(auto_attribs=True, slots=True, auto_detect=True)
class Combat(Event):
    """The cats are travelling."""

    next_event: Event
    enemies: List[NPC]
    cats_ambushed: bool = True
    enemies_ambushed: bool = False
    initiative_remaining: List[IsCatSlot] = attr.ib(factory=list)
    cats_who_have_already_acted: Set[int] = attr.ib(factory=set)
    enemies_who_have_already_acted: Set[int] = attr.ib(factory=set)
    # TODO: maybe move this to GameState
    cat_hps: Dict[int, int] = attr.ib(factory=dict)
    cat_roll_modifiers: RollModifiers = attr.ib(factory=RollModifiers)
    enemy_roll_modifiers: RollModifiers = attr.ib(factory=RollModifiers)

    @classmethod
    def start(
        cls,
        state: GameState,
        cats: List[Cat],
        next_event: Event,
        enemies: List[NPC],
        cats_ambushed: bool = True,
        enemies_ambushed: bool = False,
    ):
        """Start combat."""
        logger.info("Party starts combat.")
        enemies = [attr.evolve(enemy) for enemy in enemies]

        state.current_event = cls(
            next_event=next_event,
            enemies=enemies,
            cats_ambushed=cats_ambushed,
            enemies_ambushed=enemies_ambushed,
        )
        return DiscordMessage(
            content=f"🤼 The party gets in a fight with "
            f"{describe_npcs_list(enemies)}! 🤼",
            embed=state.current_event.make_embed(cats),
        )

    def generate_update(
        self, state: "GameState", cats: List["Cat"]
    ) -> DiscordMessage:
        cats_standing = self.cats_standing(cats)
        enemies_standing = self.enemies_standing()

        if not cats_standing:
            # TODO: go to downtime instead when defeated
            state.current_event = self.next_event
            return DiscordMessage(
                "There are no cats left standing.",
                embed=Embed(
                    colour=Colour.red(),
                    title="️⚰️ Defeat! ⚰️",
                    description="The party escapes in shame!",
                ),
            )

        if not enemies_standing:
            state.current_event = self.next_event
            return DiscordMessage(
                "There are no enemies left standing.",
                embed=Embed(
                    colour=Colour.blue(),
                    title="🏆 Victory! 🏆",
                    description="The party continues onward!",
                ),
            )

        if not self.initiative_remaining:
            return self.roll_initiative(cats_standing, enemies_standing)

        current_is_cat = self.initiative_remaining.pop(0)

        if current_is_cat:
            return self.do_cat_turn(cats_standing, enemies_standing)

        return self.do_enemy_turn(cats_standing, enemies_standing)

    def roll_initiative(
        self,
        cats_standing: List["Cat"],
        enemies_standing: List[Tuple[int, "NPC"]],
    ) -> DiscordMessage:
        """Roll initiative and reset turns already taken."""
        results = Embed(
            title="🎲 Roll initiative! 🎲",
            colour=BOT_EMBED_COLOUR,
        )
        rolls = []
        cat_messages = []
        enemy_messages = []

        # Cat rolls
        cat_skill = "Vigilance" if self.cats_ambushed else "Cool"
        for cat in cats_standing:
            dice_pool = get_cat_dice_pool(
                cat,
                att=GenesysStat.FLUFF
                if self.cats_ambushed
                else GenesysStat.PURR_VOLUME,
                skill=cat_skill,
                difficulty=0,
            )
            result = dice_pool.roll()
            rolls.append((True, result))
            cat_messages.append(
                f"🎲 {cat} rolls {dice_pool} for "
                f"{cat_skill} and gets **{result}**!"
            )

        results.add_field(
            name="😼 Party rolls 😼",
            value="\n".join(cat_messages) or "None!",
            inline=False,
        )

        # Enemy rolls
        enemy_skill = "Vigilance" if self.enemies_ambushed else "Cool"
        for _, enemy in enemies_standing:
            dice_pool = DicePool.for_skill(
                attr_value=enemy.willpower
                if self.enemies_ambushed
                else enemy.presence,
                skill_value=enemy.get_skill_value(enemy_skill),
                difficulty=0,
            )
            result = dice_pool.roll()
            rolls.append((False, result))
            enemy_messages.append(
                f"🎲 **{enemy.capname}** rolls "
                f"{dice_pool} for {enemy_skill} and gets **{result}**!"
            )

        results.add_field(
            name="👺 Enemy rolls 👺",
            value="\n".join(enemy_messages) or "None!",
            inline=False,
        )

        order = [
            is_cat
            for is_cat, roll in sorted(rolls, key=lambda r: r[1], reverse=True)
        ]

        results.add_field(
            name="🔢 Initiative order for the upcoming round 🔢",
            value=" ".join(["😼" if is_cat else "👺" for is_cat in order]),
            inline=False,
        )

        # Set initiative
        self.initiative_remaining = order
        self.cats_who_have_already_acted.clear()
        self.enemies_who_have_already_acted.clear()
        return DiscordMessage(
            "⚔️ Next round of combat starts! ⚔️", embed=results
        )

    # TODO clean this up
    # pylint: disable=R0912,R0914
    def do_cat_turn(  # noqa: C901
        self,
        cats_standing: List["Cat"],
        enemies_standing: List[Tuple[int, "NPC"]],
    ) -> DiscordMessage:
        """Have the next cat attack an enemy."""
        for c in random_order(cats_standing):
            if c.id not in self.cats_who_have_already_acted:
                logger.info("Got participant: %s", c)
                self.cats_who_have_already_acted.add(c.id)
                cat = c
                break
        else:
            logger.info("All cats have already acted")
            return DiscordMessage(
                "😼 All the remaining cats have already acted! 👺"
            )

        skill, att = random.choice(CAT_ATTACK_SKILLS)
        _, target = random.choice(enemies_standing)
        dice_pool = get_cat_dice_pool(
            cat, att, skill, difficulty=2, setback=target.defense
        )
        (
            boost_reasons,
            setback_reasons,
        ) = self.cat_roll_modifiers.apply_modifiers(dice_pool)

        dice_results = dice_pool.roll()

        messages = [
            f"🗡️ {cat} attempts to attack {target} using {cat.pronouns.his} "
            f"{skill} skill. 🗡️",
        ]

        for reason in boost_reasons:
            messages.append(f"{cat} gets a Boost die for {reason}.")

        for reason in setback_reasons:
            messages.append(f"{cat} gets a Setback die for {reason}.")

        messages.append(f"\n🎲 {cat} rolls {dice_pool}...")
        messages.append(f"\n🎲 {cat} rolled **{dice_results}**!\n")

        self.cat_roll_modifiers = RollModifiers()
        is_crit, modifier_msgs = self.handle_attack_modifiers(
            dice_results,
            crit_rating=fixed_int(f"{cat.id}_crit", 2, 6),
            attacker=cat,
        )
        messages.extend(modifier_msgs)

        if dice_results.is_success():
            damage = (
                dice_results.successes
                + dice_results.triumphs
                + 3
                + (cat.get_skill_value("damage") * 2)
            ) - dice_results.despairs
        else:
            damage = 0

        if damage:
            if is_crit:
                if target.generic:
                    messages.append(
                        f"\n⚔️ {cat} **crits and "
                        f"instantly eliminates {target}!** ⚔️"
                    )
                else:
                    damage *= 2
                    messages.append(
                        f"\n⚔️ {cat} **crits for {damage} damage!** ⚔️"
                    )
            else:
                messages.append(f"\n⚔️ {cat} hits for {damage} damage! ⚔️")
        else:
            messages.append(f"\n⚔️ {cat} misses! ⚔️")

        if damage > 0 and target.hp > 0:
            soak = target.soak
            wounds = max(0, damage - soak)
            messages.append(
                f"{target.capname} soaks {damage - wounds} "
                f"damage and takes **{wounds} {p.plural('wound', wounds)}**."
            )
            target.hp -= wounds
        if target.hp <= 0:
            messages.append(f"**{target.capname} is defeated!**")

        return DiscordMessage(
            "\n".join(messages), self.make_embed(cats_standing), cat.image
        )

    # TODO clean this up
    # pylint: disable=R0912,R0914
    def do_enemy_turn(
        self,
        cats_standing: List["Cat"],
        enemies_standing: List[Tuple[int, "NPC"]],
    ) -> DiscordMessage:
        """Execute an enemy attack."""
        for idx, npc in random_order(enemies_standing):
            if idx not in self.enemies_who_have_already_acted:
                logger.info("Got participant: %s", npc)
                self.enemies_who_have_already_acted.add(idx)
                acting = npc
                break
        else:
            logger.info("All cats have already acted")
            return DiscordMessage(
                "😼 All the remaining cats have already acted! 👺"
            )

        target: "Cat" = random.choice(cats_standing)
        dice_pool = DicePool.for_skill(
            acting.attack_attr,
            acting.attack_skill,
            difficulty=2,
            setback=fixed_int(f"{target.id}_defense", 0, 1),
        )
        (
            boost_reasons,
            setback_reasons,
        ) = self.enemy_roll_modifiers.apply_modifiers(dice_pool)

        self.enemy_roll_modifiers = RollModifiers()
        dice_results = dice_pool.roll()

        messages = [
            f"🗡️ {acting.capname} attempts to attack {target} using"
            f" their {acting.weapon}. 🗡️",
        ]

        for reason in boost_reasons:
            messages.append(f"{acting.capname} gets a Boost die for {reason}.")

        for reason in setback_reasons:
            messages.append(
                f"{acting.capname} gets a Setback die for {reason}."
            )

        messages.append(f"\n🎲 {acting.capname} rolls {dice_pool}...")
        messages.append(f"\n🎲 {acting.capname} rolled **{dice_results}**!\n")

        is_crit, modifier_msgs = self.handle_attack_modifiers(
            dice_results,
            crit_rating=fixed_int(f"{acting.weapon}_crit", 2, 4),
            attacker=acting,
        )
        messages.extend(modifier_msgs)

        if dice_results.is_success():
            damage = (
                dice_results.successes
                + dice_results.triumphs
                + acting.weapon_damage
            ) - dice_results.despairs
        else:
            damage = 0

        if damage:
            if is_crit:
                damage *= 2
                messages.append(
                    f"\n⚔️ {acting.capname} **crits for {damage} damage!** ⚔️"
                )
            else:
                messages.append(
                    f"\n⚔️ {acting.capname} hits for {damage} damage! ⚔️"
                )
        else:
            messages.append(f"\n⚔️ {acting.capname} misses! ⚔️")

        if damage > 0 and self.cat_hps[target.id] > 0:
            soak = target.soak
            wounds = max(0, damage - soak)
            messages.append(
                f"{target} soaks {damage - wounds} "
                f"damage and takes **{wounds} {p.plural('wound', wounds)}**."
            )
            self.cat_hps[target.id] -= wounds
        if self.cat_hps[target.id] <= 0:
            messages.append(f"{target} **is defeated!**")

        return DiscordMessage(
            "\n".join(messages), self.make_embed(cats_standing), target.image
        )

    def cats_standing(self, cats: List["Cat"]) -> List["Cat"]:
        """Return a list of the cats who are still alive."""
        return [
            cat
            for cat in cats
            if self.cat_hps.setdefault(cat.id, cat.wound_threshold) > 0
        ]

    def enemies_standing(self) -> List[Tuple[int, "NPC"]]:
        """
        Return a list of (index, npc) with the enemies who are still alive.
        """
        return [(i, npc) for i, npc in enumerate(self.enemies) if npc.hp > 0]

    def make_embed(self, cats: List["Cat"]) -> Embed:
        """Build an embed with an overview of the combat status."""
        cats_hps = [
            (cat, hp) for cat in cats if (hp := self.cat_hps.setdefault(cat.id, cat.wound_threshold)) > 0
        ]
        embed = Embed(
            title="⚔️ Combat! ⚔️",
            colour=BOT_EMBED_COLOUR,
        )

        cat_strs = []
        for i, (cat, hp) in enumerate(cats_hps, start=1):
            cat_str = f"{i}. {cat} [{hp}/{cat.wound_threshold}]"
            if cat.id in self.cats_who_have_already_acted:
                cat_str += " ✅"
            cat_strs.append(cat_str)

        embed.add_field(
            name="😼 Party 😼",
            value="\n".join(cat_strs) or "None remaining!",
        )

        enemies = []
        for i, (idx, npc) in enumerate(self.enemies_standing(), start=1):
            enemy_str = f"{i}. {npc.capname}"
            if idx in self.enemies_who_have_already_acted:
                enemy_str += " ✅"
            enemies.append(enemy_str)

        embed.add_field(
            name="👺 Enemies 👺",
            value="\n".join(enemies) or "None remaining!",
        )
        embed.add_field(
            name="⏱ Remaining initiative slots ⏱",
            value="".join(
                ["😼" if slot else "👺" for slot in self.initiative_remaining]
            )
            or "Rolling initiative!",
            inline=False,
        )
        return embed

    # pylint: disable=R0912,R0914,R0915
    def handle_attack_modifiers(  # noqa: C901
        self,
        roll_result: DiceResult,
        crit_rating: int,
        attacker: Union[Cat, NPC],
    ) -> Tuple[bool, List[str]]:
        """Spend advantages, threats, triumphs, and despairs."""

        # TODO: split this into smaller functions
        roll = attr.evolve(roll_result)

        is_crit = False
        messages = []

        if isinstance(attacker, Cat):
            own_modifiers = self.cat_roll_modifiers
            enemy_modifiers = self.enemy_roll_modifiers
            attacker_str = str(attacker)
        else:
            own_modifiers = self.enemy_roll_modifiers
            enemy_modifiers = self.cat_roll_modifiers
            attacker_str = attacker.capname

        # Crit first
        if roll.triumphs > 0:
            is_crit = True
            messages.append(
                f"{attacker_str} spends a Triumph to activate a crit!"
            )
            roll.triumphs -= 1

        # Spend rest of triumphs on upgrades
        enemy_upgrades = 0
        own_upgrades = 0
        while roll.triumphs > 0:
            upgrade_own = random.getrandbits(1)
            if upgrade_own:
                own_upgrades += 1
                own_modifiers.upgrades += 1
            else:
                enemy_upgrades += 1
                enemy_modifiers.difficulty_upgrades += 1
            roll.triumphs -= 1

        # Spend triumphs
        triumphs_spent = enemy_upgrades + own_upgrades
        spends_triumphs_str = (
            f"{attacker_str} spends {triumphs_spent} "
            f"{p.plural('Triumph', triumphs_spent)}"
        )
        if enemy_upgrades and own_upgrades:
            messages.append(
                f"{spends_triumphs_str} "
                f"to upgrade the next ally roll {own_upgrades}"
                f"{p.plural_noun('time', own_upgrades)} and upgrade "
                f"the difficulty of the next opponent's roll "
                f"{p.plural_noun('time', enemy_upgrades)}."
            )
        elif own_upgrades:
            messages.append(
                f"{spends_triumphs_str} "
                f"to upgrade the next ally roll {own_upgrades}"
                f"{p.plural_noun('time', own_upgrades)}."
            )
        elif enemy_upgrades:
            messages.append(
                f"{spends_triumphs_str} "
                f"to upgrade the difficulty of the next opponent's roll "
                f"{p.plural_noun('time', enemy_upgrades)}."
            )

        if (roll.advantages >= crit_rating) and not is_crit:
            is_crit = True
            messages.append(
                f"{attacker_str} spends {crit_rating} Advantages to "
                f"activate a crit!"
            )
            roll.advantages -= crit_rating

        enemy_setbacks = 0
        own_boosts = 0
        advantages_spent = roll.advantages
        while roll.advantages > 0:
            if roll.advantages >= 2:
                enemy_setbacks += 1
                enemy_modifiers.setback += 1
                roll.advantages -= 2
                continue
            own_boosts += 1
            own_modifiers.boost += 1
            continue

        spends_advantages = (
            f"{attacker_str} spends {advantages_spent} "
            f"{p.plural('Advantage', advantages_spent)}"
        )
        if enemy_setbacks and own_boosts:
            messages.append(
                f"{spends_advantages} "
                f"to grant allies {own_boosts} Boost"
                f"{p.plural_noun('die', own_boosts)} and force the "
                f"opponents to take {enemy_setbacks} Setback"
                f"{p.plural_noun('die', enemy_setbacks)} on the next roll."
            )
        elif enemy_setbacks:
            messages.append(
                f"{spends_advantages} "
                f"to force the opponents to take {enemy_setbacks} Setback"
                f"{p.plural_noun('die', enemy_setbacks)} on the next roll."
            )
        elif own_boosts:
            messages.append(
                f"{spends_advantages} to grant allies {own_boosts} Boost"
                f"{p.plural_noun('die', own_boosts)} on the next roll."
            )

        while roll.despairs > 0:
            despair = random.choice(["upgrade difficulty", "boost", "setback"])
            if despair == "upgrade difficulty":
                own_modifiers.difficulty_upgrades += 1
                messages.append(
                    f"Because {attacker} rolled a Despair, the next ally "
                    f"roll will have upgraded difficulty."
                )
            elif despair == "boost":
                enemy_modifiers.boost += 1
                messages.append(
                    f"Because {attacker} rolled a Despair, the"
                    f"opponents' next roll will get an additional Boost die."
                )
            elif despair == "setback":
                own_modifiers.setback += 1
                messages.append(
                    f"Because {attacker} rolled a Despair, the next ally "
                    f"will have to take an additional Setback die on their "
                    f"roll."
                )
            roll.despairs -= 1

        own_setbacks = 0
        enemy_boosts = 0
        disadvantages = -roll.advantages
        while disadvantages >= 2:
            add_setback = random.getrandbits(1)
            if add_setback:
                own_setbacks += 1
                own_modifiers.setback += 1
                disadvantages -= 2
                continue
            enemy_boosts += 1
            enemy_modifiers.boost += 1
            disadvantages -= 2
            continue

        if enemy_boosts:
            messages.append(
                f"{attacker_str}'s opponents get {enemy_boosts} additional "
                f"Boost {p.plural_noun('die', enemy_boosts)} on the next "
                f"roll due to the Disadvantages."
            )
        if own_setbacks:
            messages.append(
                f"{attacker_str}'s allies get {own_setbacks} additional "
                f"Setback {p.plural_noun('die', own_setbacks)} on the "
                f"next roll due to the Disadvantages."
            )

        return is_crit, messages
