# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Utilities for working with Genesys dice."""
import random
from typing import List, Tuple
from functools import total_ordering

import attr

from genesys_cats.config import config
from genesys_cats.models import Cat
from genesys_cats.util.cats import GenesysStat, percentage_to_genesys_attr
from genesys_cats.util.text import p

# Successes, Advantages, Triumphs, Despairs
BOOST = [
    (0, 0, 0, 0),
    (0, 0, 0, 0),
    (1, 0, 0, 0),
    (1, 1, 0, 0),
    (0, 2, 0, 0),
    (0, 1, 0, 0),
]

SETBACK = [
    (0, 0, 0, 0),
    (0, 0, 0, 0),
    (-1, 0, 0, 0),
    (-1, 0, 0, 0),
    (0, -1, 0, 0),
    (0, -1, 0, 0),
]

ABILITY = [
    (0, 0, 0, 0),
    (1, 0, 0, 0),
    (1, 0, 0, 0),
    (2, 0, 0, 0),
    (0, 1, 0, 0),
    (0, 1, 0, 0),
    (1, 1, 0, 0),
    (0, 2, 0, 0),
]

DIFFICULTY = [
    (0, 0, 0, 0),
    (-1, 0, 0, 0),
    (-2, 0, 0, 0),
    (0, -1, 0, 0),
    (0, -1, 0, 0),
    (0, -1, 0, 0),
    (0, -2, 0, 0),
    (-1, -1, 0, 0),
]

PROFICIENCY = [
    (0, 0, 0, 0),
    (1, 0, 0, 0),
    (1, 0, 0, 0),
    (2, 0, 0, 0),
    (2, 0, 0, 0),
    (0, 1, 0, 0),
    (1, 1, 0, 0),
    (1, 1, 0, 0),
    (1, 1, 0, 0),
    (0, 2, 0, 0),
    (0, 2, 0, 0),
    (0, 0, 1, 0),
]

CHALLENGE = [
    (0, 0, 0, 0),
    (-1, 0, 0, 0),
    (-1, 0, 0, 0),
    (-2, 0, 0, 0),
    (-2, 0, 0, 0),
    (0, -1, 0, 0),
    (0, -1, 0, 0),
    (-1, -1, 0, 0),
    (-1, -1, 0, 0),
    (0, -2, 0, 0),
    (0, -2, 0, 0),
    (0, 0, 0, 1),
]


@total_ordering
@attr.s(auto_attribs=True, slots=True, eq=True, order=False)
class DiceResult:
    """The result of a dice roll."""

    successes: int
    advantages: int
    triumphs: int = 0
    despairs: int = 0

    def is_success(self) -> bool:
        """Return whether the result is a net success."""
        return ((self.successes + self.triumphs) - self.despairs) > 0

    def __lt__(self, other) -> bool:
        if not isinstance(other, DiceResult):
            return NotImplemented
        return (
            self.successes + self.triumphs - self.despairs,
            self.advantages,
        ) < (
            other.successes + other.triumphs - other.despairs,
            other.advantages,
        )

    def __str__(self) -> str:
        results = []
        if self.successes != 0:
            if self.successes > 0:
                results.append(
                    f"{p.number_to_words(self.successes)} "
                    f"{p.plural('Success', self.successes)}"
                )
            else:
                results.append(
                    f"{p.number_to_words(-self.successes)}"
                    f" {p.plural('Failure', -self.successes)}"
                )
        if self.advantages != 0:
            if self.advantages > 0:
                results.append(
                    f"{p.number_to_words(self.advantages)} "
                    f"{p.plural('Advantage', self.advantages)}"
                )
            else:
                results.append(
                    f"{p.number_to_words(-self.advantages)}"
                    f" {p.plural('Threat', -self.advantages)}"
                )
        if self.triumphs > 0:
            results.append(
                f"{p.number_to_words(self.triumphs)} "
                f"{p.plural('Triumph', self.triumphs)}"
            )
        if self.despairs > 0:
            results.append(
                f"{p.number_to_words(self.despairs)} "
                f"{p.plural('Despair', self.despairs)}"
            )
        if not results:
            return "a wash"
        if len(results) == 1:
            return results[0]
        if len(results) == 2:
            return f"{results[0]} and {results[1]}"
        return ", ".join(results[:-1]) + f", and {results[-1]}"


@attr.s(auto_attribs=True, slots=True, auto_detect=True)
class DicePool:
    """A pool of dice."""

    ability: int = 0
    proficiency: int = 0
    difficulty: int = 0
    challenge: int = 0
    boost: int = 0
    setback: int = 0

    @classmethod
    def for_skill(  # pylint:disable=too-many-arguments
        cls,
        attr_value: int,
        skill_value: int,
        difficulty: int = 2,
        challenge: int = 0,
        boost: int = 0,
        setback: int = 0,
    ):
        """
        Return the appropriate DicePool for a skill and attribute (and
        opposed skill and attribute, represented by difficulty and challenge
        dice), by upgrading the appropriate number of Ability dice to
        Proficiency dice, and Difficulty dice to Challenge dice.
        """
        proficiency_dice = min(skill_value, attr_value)
        challenge_dice = min(difficulty, challenge)
        return cls(
            ability=max(skill_value, attr_value) - proficiency_dice,
            proficiency=proficiency_dice,
            difficulty=max(difficulty, challenge) - challenge_dice,
            challenge=challenge_dice,
            boost=boost,
            setback=setback,
        )

    def upgrade(self, times: int = 1) -> "DicePool":
        """Upgrade or downgrade the dice."""
        upgrades_remaining = times

        # Upgrade
        while upgrades_remaining > 0:
            if self.ability > 0:
                self.ability -= 1
                self.proficiency += 1
            else:
                self.ability += 1
            upgrades_remaining -= 1

        # Downgrade
        while upgrades_remaining < 0:
            if self.proficiency > 0:
                self.proficiency -= 1
                self.ability += 1
                upgrades_remaining += 1
            else:
                # Downgrading never removes dice
                break

        return self

    def upgrade_difficulty(self, times: int = 1) -> "DicePool":
        """Upgrade or downgrade the difficulty."""
        upgrades_remaining = times

        # Upgrade
        while upgrades_remaining > 0:
            if self.difficulty > 0:
                self.difficulty -= 1
                self.challenge += 1
            else:
                self.difficulty += 1
            upgrades_remaining -= 1

        # Downgrade
        while upgrades_remaining < 0:
            if self.challenge > 0:
                self.challenge -= 1
                self.difficulty += 1
                upgrades_remaining += 1
            else:
                # Downgrading never removes dice
                break

        return self

    def roll(self) -> DiceResult:
        """Roll this DicePool and return a DiceResult."""
        dice_results = (
            random.choices(ABILITY, k=self.ability)
            + random.choices(PROFICIENCY, k=self.proficiency)
            + random.choices(DIFFICULTY, k=self.difficulty)
            + random.choices(CHALLENGE, k=self.challenge)
            + random.choices(BOOST, k=self.boost)
            + random.choices(SETBACK, k=self.setback)
        )
        successes, advantages, triumphs, despairs = zip(*dice_results)
        return DiceResult(
            successes=sum(successes),
            advantages=sum(advantages),
            triumphs=sum(triumphs),
            despairs=sum(despairs),
        )

    def __str__(self) -> str:
        dice_words = []
        if self.ability:
            dice_words.append(
                f"{p.number_to_words(self.ability)} Ability "
                f"{p.plural('die', self.ability)}"
            )
        if self.proficiency:
            dice_words.append(
                f"{p.number_to_words(self.proficiency)} Proficiency "
                f"{p.plural('die', self.proficiency)}"
            )
        if self.difficulty:
            dice_words.append(
                f"{p.number_to_words(self.difficulty)} Difficulty"
                f" {p.plural('die', self.difficulty)}"
            )

        if self.challenge:
            dice_words.append(
                f"{p.number_to_words(self.challenge)} Challenge"
                f" {p.plural('die', self.challenge)}"
            )
        if self.boost:
            dice_words.append(
                f"{p.number_to_words(self.boost)} Boost"
                f" {p.plural('die', self.boost)}"
            )
        if self.setback:
            dice_words.append(
                f"{p.number_to_words(self.setback)} Setback "
                f"{p.plural('die', self.setback)}"
            )
        if not dice_words:
            return "no dice"
        if len(dice_words) == 1:
            return dice_words[0]
        if len(dice_words) == 2:
            return f"{dice_words[0]} and {dice_words[1]}"
        return ", ".join(dice_words[:-1]) + f", and {dice_words[-1]}"


def get_cat_dice_pool(  # pylint:disable=too-many-arguments
    cat: Cat,
    att: GenesysStat,
    skill: str,
    difficulty: int = 2,
    challenge: int = 0,
    boost: int = 0,
    setback: int = 0,
) -> DicePool:
    """Get the dice pool for a cat attribute and skill."""
    skill_val = cat.get_skill_value(skill)
    att_val = percentage_to_genesys_attr(getattr(cat, att.value))
    return DicePool.for_skill(
        att_val, skill_val, difficulty, challenge, boost, setback
    )


RANDOM_BOOST_REASONS = [
    "being a great cat",
    "being based",
    "being high on catnip",
    "being in an excellent mood",
    "cuteness",
    "being focused",
    "having recently eaten",
    "impeccable vibes",
]

RANDOM_SETBACK_REASONS = [
    "discourse",
    "horniness",
    "having rotten vibes",
    "being distracted",
]


def grant_random_bonus_dice(
    dice_pool: DicePool,
) -> Tuple[List[str], List[str]]:
    """
    Grant random bonus dice, mutating the dice pool in place, and return the
    lists of reasons for boost and setback dice.
    """
    boost = 0
    if random.random() < config.gm_bonus_die_chance:
        boost = 1
        if random.random() < config.gm_bonus_die_chance:
            boost = 2

    dice_pool.boost += boost
    boost_reasons = []
    if boost:
        boost_reasons = random.sample(RANDOM_BOOST_REASONS, k=boost)

    setback = 0
    if random.random() < config.gm_bonus_die_chance:
        setback = 1
        if random.random() < config.gm_bonus_die_chance:
            setback = 2

    dice_pool.setback += setback
    setback_reasons = []
    if setback:
        setback_reasons = random.sample(RANDOM_SETBACK_REASONS, k=setback)
    return boost_reasons, setback_reasons
