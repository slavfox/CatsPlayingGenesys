# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Database models."""
from typing import TYPE_CHECKING

from tortoise import Model, fields

from genesys_cats.util.cats import (
    CAT_BODY_IMAGE,
    CAT_EYES_IMAGE,
    highlight_stat,
    percentage_to_genesys_attr,
    personality_title,
)
from genesys_cats.util.image import color_image
from genesys_cats.util.rng import fixed_int
from genesys_cats.util.text import Pronouns

if TYPE_CHECKING:
    from PIL import Image


class Server(Model):
    """Discord Server model."""

    id = fields.IntField(pk=True)
    discord_id = fields.BigIntField()
    cat_channel_id = fields.BigIntField(null=True, default=None)
    command_channel_id = fields.BigIntField(null=True, default=None)
    current_adoptable_cat: fields.ForeignKeyNullableRelation[
        "Cat"
    ] = fields.ForeignKeyField(
        "models.Cat", null=True, on_delete=fields.SET_NULL
    )
    genesys_state = fields.JSONField(default=None, null=True)

    users: fields.ManyToManyRelation["User"]

    def __str__(self) -> str:
        return f"Server {self.id}: {self.discord_id}"


class User(Model):
    """Discord User model."""

    id = fields.IntField(pk=True)
    discord_id = fields.BigIntField()
    servers: fields.ManyToManyRelation["Server"] = fields.ManyToManyField(
        "models.Server", related_name="users", through="user_servers"
    )

    cats: fields.ReverseRelation["Cat"]

    def __str__(self) -> str:
        return f"User {self.id}: {self.discord_id}"


class Cat(Model):
    """A cat."""

    id = fields.IntField(pk=True)
    name = fields.TextField()
    owner: fields.ForeignKeyNullableRelation["User"] = fields.ForeignKeyField(
        "models.User",
        null=True,
        default=None,
        on_delete=fields.SET_NULL,
        related_name="cats",
    )
    pronouns_csv = fields.TextField()
    descriptor = fields.TextField()
    likes = fields.TextField()
    dislikes = fields.TextField()
    hobby = fields.TextField()
    # Colors
    body_r = fields.SmallIntField()
    body_g = fields.SmallIntField()
    body_b = fields.SmallIntField()
    eyes_r = fields.SmallIntField()
    eyes_g = fields.SmallIntField()
    eyes_b = fields.SmallIntField()
    # === Stats ===
    # Brawn
    chonk = fields.SmallIntField()
    # Agility
    zoomies = fields.SmallIntField()
    # Intellect
    curiosity = fields.SmallIntField()
    # Cunning
    playfulness = fields.SmallIntField()
    # Willpower
    fluff = fields.SmallIntField()
    # Presence
    purr_volume = fields.SmallIntField()
    # === Personality ===
    # Feline Five
    # How anxious the cat is
    skittishness = fields.SmallIntField()
    # How likely the cat is to seek new experiences
    outgoingness = fields.SmallIntField()
    # How likely the cat is to lead or assume a dominant social role
    dominance = fields.SmallIntField()
    # How impulsive the cat is
    spontaneity = fields.SmallIntField()
    # How affectionate the cat is
    friendliness = fields.SmallIntField()

    def __str__(self) -> str:
        return f"**{self.name}** (#{self.id})"

    @property
    def pronouns(self) -> "Pronouns":
        """This cat's pronouns."""
        return Pronouns.from_pronoun_string(self.pronouns_csv)

    @property
    def title(self) -> str:
        """This cat's CK3-style personality title."""
        return personality_title(self)

    @property
    def highlight_genesys_stat(self) -> str:
        """Describe this cat's most extreme Genesys stat."""
        return highlight_stat(self)

    @property
    def image(self) -> "Image.Image":
        """This cat's image."""
        cat_body_image = color_image(
            (self.body_r, self.body_g, self.body_b), CAT_BODY_IMAGE
        )
        cat_eyes_image = color_image(
            (self.eyes_r, self.eyes_g, self.eyes_b), CAT_EYES_IMAGE
        )
        cat_body_image.paste(cat_eyes_image, (0, 0), cat_eyes_image)
        return cat_body_image

    @property
    def wound_threshold(self) -> int:
        """Return the cat's wound threshold."""
        base = fixed_int(f"{self.id}_wound_threshold_base", min_=8, max_=12)
        bonuses = fixed_int(f"{self.id}_wound_threshold_bonus", min_=0, max_=1)
        return base + bonuses + percentage_to_genesys_attr(self.chonk)

    @property
    def strain_threshold(self) -> int:
        """Return the cat's strain threshold."""
        # this is intentionally based on wound threshold
        wound_threshold_base = fixed_int(
            f"{self.id}_wound_threshold_base", min_=8, max_=12
        )
        bonuses = fixed_int(
            f"{self.id}_strain_threshold_bonus", min_=0, max_=1
        )
        return (
            8
            + (12 - wound_threshold_base)
            + bonuses
            + percentage_to_genesys_attr(self.fluff)
        )

    @property
    def soak(self) -> int:
        """Return this cat's soak value."""
        return percentage_to_genesys_attr(self.chonk)

    def get_skill_value(self, skill: str) -> int:
        """Get the value for a skill."""
        return fixed_int(f"{self.id}_{skill}", min_=0, max_=3)
