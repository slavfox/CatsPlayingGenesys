# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Utilities for bot use."""
from typing import Optional, Tuple, cast
from io import BytesIO
from logging import getLogger

import discord
from tortoise.exceptions import OperationalError
from tortoise.transactions import in_transaction

from genesys_cats.models import Cat, Server
from genesys_cats.util.catgen import generate_cat
from genesys_cats.util.cats import build_cat_message
from genesys_cats.util.discord import make_cat_embed

logger = getLogger("bot_helpers")


async def get_server(message: discord.Message) -> "Server":
    """Get or create the Server obj for a given Message."""
    server_obj = (
        await Server.filter(discord_id=message.guild.id)
        .prefetch_related("current_adoptable_cat")
        .get_or_none()
    )
    if not server_obj:
        server_obj = Server(
            discord_id=message.guild.id,
            command_channel_id=message.channel.id,
        )
        await server_obj.save()
    return server_obj


async def try_send(message: discord.Message, *args, **kwargs):
    """
    Attempt to reply to a message in a channel, and DM the author if the
    bot does not have sufficient permissions to reply in-channel.
    """
    try:
        return await message.channel.send(*args, **kwargs)
    except discord.Forbidden:
        await message.add_reaction("📨")
        return await message.author.send(*args, **kwargs)


BOT_EMBED_COLOUR = discord.Colour.from_rgb(254, 200, 193)


async def send_cat(
    channel: discord.TextChannel, cat: "Cat", content: Optional[str] = None
):
    """Send a cat to a channel, with a given message."""
    embed = make_cat_embed(cat)
    f = BytesIO()
    cat.image.save(f, "PNG")
    f.seek(0)
    return await channel.send(
        content=content,
        file=discord.File(f, filename="cat.png"),
        embed=embed,
    )


async def spawn_new_cat(
    server: Server, invited_by: Optional["Cat"] = None
) -> Tuple[Cat, str]:
    """Spawn a new cat, and return the cat and a spawn message."""
    cat = generate_cat()
    try:
        async with in_transaction() as connection:
            current_adoptable_cat = cast(
                Optional["Cat"], server.current_adoptable_cat
            )
            message = build_cat_message(cat, current_adoptable_cat, invited_by)
            if current_adoptable_cat is not None:
                await current_adoptable_cat.delete(using_db=connection)
            await cat.save(using_db=connection)
            server.current_adoptable_cat = cat
            await server.save(using_db=connection)
    except OperationalError as err:
        logger.exception(err)
        raise err
    return cat, message
