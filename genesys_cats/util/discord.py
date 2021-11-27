# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Discord-related utilities."""
from typing import TYPE_CHECKING, Optional
from io import BytesIO

import attr
import discord
from discord import Colour, Embed
from PIL.Image import Image

from genesys_cats.util.cats import percentage_to_genesys_attr
from genesys_cats.util.text import p

if TYPE_CHECKING:
    from genesys_cats.models import Cat


@attr.s(auto_attribs=True, slots=True, auto_detect=True, frozen=True)
class DiscordMessage:
    """A Discord message that may include an embed or image."""

    content: Optional[str] = None
    embed: Optional[Embed] = None
    image: Optional[Image] = None

    async def send(self, channel: discord.TextChannel) -> None:
        """Send this message to a given channel."""
        if self.image is not None:
            f = BytesIO()
            self.image.save(f, "PNG")
            f.seek(0)
            image = discord.File(f, filename="image.png")
        else:
            image = None
        await channel.send(
            content=self.content,
            embed=self.embed,
            file=image,
        )

    def with_content(self, content: str) -> "DiscordMessage":
        """Return a copy of this message with the given content."""
        return attr.evolve(self, content=content)

    def with_embed(self, embed: Embed) -> "DiscordMessage":
        """Return a copy of the message with the embed replaced."""
        return attr.evolve(self, embed=embed)

    def with_image(self, image: Image) -> "DiscordMessage":
        """Return a copy of this message with the image swapped out."""
        return attr.evolve(self, image=image)


def percentage_to_moons(stat: int) -> str:
    """
    Convert a percentage stat (from the db) to moons representing the Genesys
    value.
    """
    genesys = percentage_to_genesys_attr(stat)
    return genesys * "🌕" + (4 - genesys) * "🌑"


def make_cat_embed(cat: "Cat") -> Embed:
    """Build an embed for displaying this cat."""
    pr = cat.pronouns

    # An X cat of considerable Y.
    tagline = (
        f"{p.a(cat.descriptor).capitalize()} cat of "
        f"{cat.highlight_genesys_stat}."
    )

    # They like X and dislike Y.
    likes = "like" if pr.plural else "likes"
    likes_str = (
        f"{pr.he.capitalize()} {likes} {cat.likes} "
        f"and dis{likes} {cat.dislikes}."
    )

    # They spend their free time doing X.
    spends = "spend" if pr.plural else "spends"
    hobby_str = (
        f"{pr.he.capitalize()} {spends} {pr.his} free time {cat.hobby}."
    )
    cat_embed = Embed(
        title=f"{cat.id}. 🐱 {cat.name}, the {cat.title} 🐱",
        description=f"{tagline}\n{likes_str}\n{hobby_str}",
        colour=Colour.from_rgb(cat.eyes_r, cat.eyes_g, cat.eyes_b),
    )
    cat_embed.add_field(name="Breed 🐈", value="cat", inline=False)

    cat_embed.add_field(
        name="Chonk 🍔", value=percentage_to_moons(cat.chonk), inline=True
    )
    cat_embed.add_field(
        name="Zoomies 💫",
        value=percentage_to_moons(cat.zoomies),
        inline=True,
    )
    cat_embed.add_field(
        name="Curiosity 🤓",
        value=percentage_to_moons(cat.curiosity),
        inline=True,
    )
    cat_embed.add_field(
        name="Playfulness 🧶",
        value=percentage_to_moons(cat.playfulness),
        inline=True,
    )
    cat_embed.add_field(
        name="Fluff 💇", value=percentage_to_moons(cat.fluff), inline=True
    )
    cat_embed.add_field(
        name="Purr Volume 🔊",
        value=percentage_to_moons(cat.purr_volume),
        inline=True,
    )
    cat_embed.add_field(
        name="Purr Volume 🔊",
        value=percentage_to_moons(cat.purr_volume),
        inline=True,
    )
    cat_embed.add_field(
        name="Wound Threshold ❤️‍🩹",
        value=str(cat.wound_threshold),
        inline=False,
    )

    return cat_embed
