# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Cat-related utilities and common constants."""
from typing import TYPE_CHECKING, NamedTuple, Optional
from enum import Enum

import numpy as np
from PIL import Image

from genesys_cats.config import ASSETS_DIR

if TYPE_CHECKING:
    from typing import Dict

    from genesys_cats.models import Cat


class PersonalityStat(Enum):
    """Personality stats, Feline Five."""

    # How anxious the cat is
    SKITTISHNESS = "skittishness"
    # How likely the cat is to seek out new experiences
    OUTGOINGNESS = "outgoingness"
    # How likely the cat is to lead or assume a dominant social role
    DOMINANCE = "dominance"
    # How impulsive the cat is
    SPONTANEITY = "spontaneity"
    # How affectionate the cat is
    FRIENDLINESS = "friendliness"


class GenesysStat(Enum):
    """Genesys attributes."""

    # Brawn
    CHONK = "chonk"
    # Agility
    ZOOMIES = "zoomies"
    # Intellect
    CURIOSITY = "curiosity"
    # Cunning
    PLAYFULNESS = "playfulness"
    # Willpower
    FLUFF = "fluff"
    # Presence
    PURR_VOLUME = "purr_volume"


CAT_BODY_IMAGE = np.array(
    Image.open(str(ASSETS_DIR / "cat_body.png")).convert("RGBA")
)
CAT_EYES_IMAGE = np.array(
    Image.open(str(ASSETS_DIR / "cat_eyes.png")).convert("RGBA")
)


class _Titles(NamedTuple):
    """Descriptors for a personality stat."""

    very_low: str
    low: str
    high: str
    very_high: str


# fmt: off
PERSONALITY_ADJECTIVES = {
    PersonalityStat.SKITTISHNESS: _Titles(
        very_low="laid-back",
        low="calm",
        high="nervous",
        very_high="skittish"
    ),
    PersonalityStat.OUTGOINGNESS: _Titles(
        very_low="shy",
        low="timid",
        high="outgoing",
        very_high="adventurous"
    ),
    PersonalityStat.DOMINANCE: _Titles(
        very_low="docile",
        low="loyal",
        high="leading",
        very_high="dominant"
    ),
    PersonalityStat.SPONTANEITY: _Titles(
        very_low="reliable",
        low="well-mannered",
        high="playful",
        very_high="mischievous",
    ),
    PersonalityStat.FRIENDLINESS: _Titles(
        very_low="solitary",
        low="aloof",
        high="friendly",
        very_high="cuddly"
    ),
}
PERSONALITY_TITLES = {
    PersonalityStat.SKITTISHNESS: _Titles(
        very_low="cool cat",
        low="cat",
        high="scaredy-cat",
        very_high="coward"
    ),
    PersonalityStat.OUTGOINGNESS: _Titles(
        very_low="couch potato",
        low="napper",
        high="curious cat",
        very_high="adventurer",
    ),
    PersonalityStat.DOMINANCE: _Titles(
        very_low="pushover",
        low="sidekick",
        high="leader",
        very_high="bully"
    ),
    PersonalityStat.SPONTANEITY: _Titles(
        very_low="planner",
        low="schemer",
        high="rogue",
        very_high="troublemaker",
    ),
    PersonalityStat.FRIENDLINESS: _Titles(
        very_low="loner",
        low="alley cat",
        high="buddy",
        very_high="companion"
    ),
}
# fmt: on


def get_descriptor(
    descriptors: "Dict[PersonalityStat, _Titles]",
    stat: "PersonalityStat",
    value: int,
) -> str:
    """
    Get an appropriate cat personality title part for a given stat and value.
    """
    if value < -25:
        return descriptors[stat].very_low
    if value < 0:
        return descriptors[stat].low
    if value < 25:
        return descriptors[stat].high
    return descriptors[stat].very_high


def personality_title(cat: "Cat") -> "str":
    """Generate a personality title for a cat."""
    personality: "Dict[PersonalityStat, int]" = {
        stat: getattr(cat, stat.value) - 50 for stat in PersonalityStat
    }
    most_extreme_stat = PersonalityStat.SKITTISHNESS
    most_extreme_val = 0
    second_most_extreme_stat = PersonalityStat.SKITTISHNESS
    second_most_extreme_val = 0
    for stat, value in personality.items():
        if abs(value) > abs(most_extreme_val):
            second_most_extreme_val = most_extreme_val
            second_most_extreme_stat = most_extreme_stat
            most_extreme_stat = stat
            most_extreme_val = value
        elif abs(value) > abs(second_most_extreme_val):
            second_most_extreme_val = value
            second_most_extreme_stat = stat
    adj = get_descriptor(
        PERSONALITY_ADJECTIVES,
        second_most_extreme_stat,
        second_most_extreme_val,
    )
    title = get_descriptor(
        PERSONALITY_TITLES, most_extreme_stat, most_extreme_val
    )
    return f"{adj} {title}"


def highlight_stat(cat: "Cat") -> str:
    """Describe a cat's standout Genesys stat."""
    most_extreme_stat, most_extreme_val = max(
        [(stat, getattr(cat, stat.value)) for stat in GenesysStat],
        key=lambda stat: abs(stat[1] - 50),
    )
    if most_extreme_val < 25:
        quantifier = "low"
    elif most_extreme_val < 50:
        quantifier = "below average"
    elif most_extreme_val < 75:
        quantifier = "considerable"
    else:
        quantifier = "extreme"
    return f"{quantifier} {most_extreme_stat.value.replace('_', ' ').title()}"


def percentage_to_genesys_attr(value: int) -> int:
    """Convert a value between 0 and 100 to one between 1 and 4."""
    if value >= 85:
        return 4
    if value >= 65:
        return 3
    if value >= 25:
        return 2
    return 1


def build_cat_message(
    new_cat: "Cat",
    previous_cat: Optional["Cat"] = None,
    invited_by: Optional["Cat"] = None,
) -> str:
    """
    Generic message for new cats.

    ``previous_cat`` is the previous adoptable cat, for a "<previous cat>
    left!" note.

    ``invited_by`` is a cat to be displayed in a "<invited_by> invited their
    friend, <new_cat> to the table!"
    """
    content = ""
    if invited_by:
        content += (
            f"{invited_by} invited {invited_by.pronouns.his} "
            f"friend to the table!\n"
        )
    if previous_cat and previous_cat != new_cat:
        content += f"{previous_cat} left!\n\n"
    content += (
        f"🐈 **{new_cat.name}** 🐈\n"
        f"Type `catbot: adopt` to adopt {new_cat.pronouns.him}."
    )
    return content
