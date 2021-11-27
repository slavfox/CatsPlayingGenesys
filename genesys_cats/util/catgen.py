# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Cat generation"""
import random
from typing import Tuple

from genesys_cats.models import Cat
from genesys_cats.util.catgen_data import (
    CAT_DESCRIPTORS,
    CAT_HOBBIES,
    CAT_LIKES_DISLIKES,
    CAT_NAMES,
    CAT_PREFIXES,
    CAT_PRONOUNS,
    CAT_SUFFIXES,
)
from genesys_cats.util.image import hsl_to_rgb
from genesys_cats.util.rng import normal_integer_0_100
from genesys_cats.util.text import Pronouns, replace_pronouns

PREFIX_CHANCE = 0.075
SUFFIX_CHANCE = 0.15


def generate_cat_name() -> str:
    """Generate a new cat name."""
    name = random.choice(CAT_NAMES)
    if random.random() < PREFIX_CHANCE:
        name = f"{random.choice(CAT_PREFIXES)} {name}"
    if random.random() < SUFFIX_CHANCE:
        name = f"{name} {random.choice(CAT_SUFFIXES)}"
    return name


def generate_cat_body_color_hsl() -> Tuple[int, int, int]:
    """Generate a brownish HSL color for a cat body."""
    hue = random.randint(10, 45)
    saturation = random.randint(0, 100)
    lightness = round((random.random() ** 2) * 100)
    return hue, saturation, lightness


def generate_cat_eye_color_hsl(body_lightness: int) -> Tuple[int, int, int]:
    """Generate an appropriate HSL color for cat eyes."""
    hue = random.randint(0, 360)
    saturation = random.randint(0, 100)
    if body_lightness < 50:
        lightness = random.randint(50, 90)
    else:
        lightness = random.randint(0, 30)
    return hue, saturation, lightness


def generate_cat() -> "Cat":
    """Generate a new cat."""
    name = generate_cat_name()
    pronouns_csv = random.choice(CAT_PRONOUNS)
    pronouns = Pronouns.from_pronoun_string(pronouns_csv)
    likes, dislikes = random.sample(CAT_LIKES_DISLIKES, 2)
    hobby = replace_pronouns(random.choice(CAT_HOBBIES), pronouns)
    descriptor = random.choice(CAT_DESCRIPTORS)
    body_hsl = generate_cat_body_color_hsl()
    eyes_hsl = generate_cat_eye_color_hsl(body_hsl[2])
    body_r, body_g, body_b = hsl_to_rgb(*body_hsl)
    eyes_r, eyes_g, eyes_b = hsl_to_rgb(*eyes_hsl)
    return Cat(
        name=name,
        pronouns_csv=pronouns_csv,
        descriptor=descriptor,
        likes=likes,
        dislikes=dislikes,
        hobby=hobby,
        body_r=body_r,
        body_g=body_g,
        body_b=body_b,
        eyes_r=eyes_r,
        eyes_g=eyes_g,
        eyes_b=eyes_b,
        chonk=normal_integer_0_100(),
        zoomies=normal_integer_0_100(),
        curiosity=normal_integer_0_100(),
        playfulness=normal_integer_0_100(),
        fluff=normal_integer_0_100(),
        purr_volume=normal_integer_0_100(),
        skittishness=normal_integer_0_100(),
        outgoingness=normal_integer_0_100(),
        dominance=normal_integer_0_100(),
        spontaneity=normal_integer_0_100(),
        friendliness=normal_integer_0_100(),
    )
