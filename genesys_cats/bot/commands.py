# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Bot commands."""
# pylint: disable=unused-argument
import re
from typing import Awaitable, Callable, Dict, Optional, cast
from functools import wraps
from io import BytesIO
from logging import getLogger

import discord
from tortoise.exceptions import OperationalError
from tortoise.transactions import in_transaction

from genesys_cats.bot.helpers import (
    BOT_EMBED_COLOUR,
    get_server,
    send_cat,
    try_send,
)
from genesys_cats.config import config
from genesys_cats.models import Cat, Server, User
from genesys_cats.util.cats import build_cat_message
from genesys_cats.util.text import p

CommandType = Callable[[discord.Client, str, discord.Message], Awaitable[None]]
COMMANDS: Dict["re.Pattern[str]", "CommandType"] = {}
logger = getLogger("commands")


HELP_EMBED = discord.Embed(
    title="🎲 Cats Playing Genesys 🎲",
    description="Available commands:",
    colour=BOT_EMBED_COLOUR,
)


def register_command(regex: str, human_readable: str, description: str):
    """Register a command to a regex."""

    def decorator(f: CommandType) -> CommandType:
        COMMANDS[re.compile(regex)] = f
        HELP_EMBED.add_field(
            name=f"catbot: {human_readable}", value=description, inline=False
        )
        return f

    return decorator


def admin_only(cmd: CommandType) -> CommandType:
    """Restrict a command to server admins."""

    @wraps(cmd)
    async def decorated(
        bot: discord.Client, command: str, message: discord.Message
    ) -> None:
        if not message.author.guild_permissions.administrator:
            await message.add_reaction("❌")
            return await message.channel.send(
                "❌ This is an admin-only command!"
            )
        return await cmd(bot, command, message)

    return decorated


def command_channel_only(
    cmd: Callable[
        [discord.Client, str, discord.Message, Server], Awaitable[None]
    ]
) -> CommandType:
    """Restrict a command to the command channel."""

    @wraps(cmd)
    async def decorated(
        bot: discord.Client, command: str, message: discord.Message
    ) -> None:
        server = await get_server(message)
        if (
            server.command_channel_id is None
            or server.command_channel_id != message.channel.id
        ):
            return
        return await cmd(bot, command, message, server)

    return decorated


async def handle_command(
    bot: discord.Client, message: discord.Message
) -> None:
    """Dispatch to the appropriate command coroutine."""
    command = message.content.lower()[len(config.prefix) :].strip()
    for regex, coro in COMMANDS.items():
        if regex.match(command):
            return await coro(bot, command, message)
    await message.add_reaction("❌")
    await message.channel.send("❌ Invalid command!")
    raise ValueError(f"Invalid command: {message.content}")


@register_command("^help$", "help", "Show this message.")
async def show_help(
    bot: discord.Client, command: str, message: discord.Message
) -> None:
    """Show the help embed."""
    return await try_send(message, embed=HELP_EMBED)


@register_command(
    "^set command channel$",
    "set command channel (admin only)",
    "Set the channel to be used for interaction with the bot.",
)
@admin_only
async def set_command_channel(
    bot: discord.Client, command: str, message: discord.Message
) -> None:
    """Set the command channel."""
    server_obj = await get_server(message)
    if server_obj.command_channel_id == message.channel.id:
        await try_send(
            message,
            "⚠️ Failed: This channel is already being used for commands!",
        )
        return
    server_obj.command_channel_id = message.channel.id
    await server_obj.save()
    await message.add_reaction("✅")
    embed = discord.Embed(
        title="✅ Success!",
        description=f"{message.channel.mention} will now be used for  "
        f"command output.",
    )
    embed.add_field(
        name="🐱 Adopting a cat 🐱",
        value="Cats will invite friends to play from time to time. You "
        "can adopt a cat that shows up randomly through the "
        "`catbot: adopt` command.\n\nType `catbot: help` for a list of "
        "the available commands.",
    )
    await try_send(message, embed=HELP_EMBED)
    return


@register_command(
    "^set dice channel$",
    "set dice channel (admin only)",
    "Set the channel to be used by the cats to play RPGs.",
)
@admin_only
async def set_dice_channel(
    bot: discord.Client, command: str, message: discord.Message
) -> None:
    """Set the cat channel."""
    server_obj = await get_server(message)
    if server_obj.cat_channel_id == message.channel.id:
        await try_send(
            message,
            "⚠️ Failed: This channel is already being used by the cats to "
            "play RPGs!",
        )
        return
    server_obj.cat_channel_id = message.channel.id
    await server_obj.save()
    await message.add_reaction("✅")
    embed = discord.Embed(
        title="✅ Success!",
        description=f"{message.channel.mention} will now be used by "
        f"the cats to play RPGs.",
    )
    embed.add_field(
        name="🐱 Adopting a cat 🐱",
        value="Cats will invite friends to play from time to time. You "
        "can adopt a cat that shows up randomly through the "
        "`catbot: adopt` command.\n\nType `catbot: help` for a list of "
        "the available commands.",
    )
    await try_send(message, embed=HELP_EMBED)
    return


@register_command(
    "^adopt$",
    "adopt",
    "Adopt the current adoptable cat, if any.",
)
async def adopt(
    bot: discord.Client, command: str, message: discord.Message
) -> None:
    """Adopt the last adoptable cat, if any."""
    server_obj = await get_server(message)
    if server_obj.command_channel_id is None:
        return
    logger.info("Adopt cat called")
    cat = cast(Optional[Cat], server_obj.current_adoptable_cat)
    logger.info("got cat %s", cat)
    if cat is None:
        await message.add_reaction("❌")
        await bot.get_channel(server_obj.command_channel_id).send(
            f"❌ {message.author.mention}, "
            f"there are no adoptable cats at the moment."
        )
        return
    try:
        async with in_transaction() as connection:
            owner, _ = await User.get_or_create(discord_id=message.author.id)
            cnt = await owner.cats.all().count()
            if cnt >= 3:
                await message.add_reaction("❌")
                await bot.get_channel(server_obj.command_channel_id).send(
                    f"❌ {message.author.mention}, "
                    f"you cannot have more than 3 cats."
                )
                return
            await owner.servers.add(server_obj)
            await owner.save(using_db=connection)
            cat.owner = owner
            await cat.save(using_db=connection)
            server_obj.current_adoptable_cat = None
            await server_obj.save(using_db=connection)
    except OperationalError as err:
        await message.add_reaction("⚠️")
        logger.exception(err)
        await try_send(message, "Something went wrong; try again later.")
        raise RuntimeError("DB error.") from err
    cat_count = await Cat.filter(owner=owner).count()
    f = BytesIO()
    cat.image.save(f, "PNG")
    f.seek(0)
    await message.add_reaction("✅")
    await bot.get_channel(server_obj.command_channel_id).send(
        content=f"💝 {message.author.mention}, "
        f"you have adopted **{cat.name}**, cat #{cat.id}! 💝\n"
        f"You now have {p.number_to_words(cat_count)} "
        f"{p.plural('cat', cat_count)}.",
        file=discord.File(f, filename="cat.png"),
    )
    return


@register_command(
    r"^show$",
    "show",
    "Show all owned cats.",
)
@command_channel_only
async def show_cats(
    bot: discord.Client, command: str, message: discord.Message, server: Server
) -> None:
    """Show all owned cats."""
    logger.info("command: show")
    cats = await Cat.filter(
        owner__discord_id=message.author.id,
    ).order_by("id")
    description = [
        f"{cat.id}. 🐱 **{cat.name}**, the {cat.title}" for cat in cats
    ]
    embed = discord.Embed(
        title=f"🐈 {message.author.nick}'s cats 🐈",
        description="\n".join(description),
        colour=BOT_EMBED_COLOUR,
    )
    embed.set_footer(
        text="Type `catbot: show <id>` to see the details for a specific "
        "cat."
    )
    await bot.get_channel(server.command_channel_id).send(
        content=f"Here are the cats you currently have, "
        f"{message.author.mention}.",
        embed=embed,
    )
    return


@register_command(
    r"^show \d+$",
    "show <number>",
    "Show the details for a specific cat.",
)
@command_channel_only
async def show_cat_id(
    bot: discord.Client, command: str, message: discord.Message, server: Server
) -> None:
    """Show details for a specific cat."""
    logger.info("command: %s", command)
    cat_id = int(command.split(maxsplit=1)[1])
    logger.info("showing %s", cat_id)
    cat = await Cat.filter(
        id=cat_id,
    ).first()
    if not cat:
        await message.add_reaction("❌")
        await bot.get_channel(server.command_channel_id).send(
            f"❌ There is no cat with id {cat_id}!"
        )
        return
    await send_cat(
        bot.get_channel(server.command_channel_id),
        cat,
        f"{message.author.mention}, here's cat #{cat.id}: 🐈 **{cat.name}** 🐈",
    )
    return


@register_command(
    r"^current cat$",
    "current cat",
    "Show the current adoptable cat, if any.",
)
@command_channel_only
async def current_cat(
    bot: discord.Client, command: str, message: discord.Message, server: Server
) -> None:
    """Show the last adoptable cat, if any."""
    logger.info("command: current cat")
    cat = cast(Optional[Cat], server.current_adoptable_cat)
    if cat is not None:
        await send_cat(message.channel, cat, build_cat_message(cat))
    await message.channel.send("❌ There are no adoptable cats at the moment.")
    return


@register_command(
    r"^release \d+$",
    "release <number>",
    "Release a cat you own.",
)
@command_channel_only
async def release_cat_id(
    bot: discord.Client, command: str, message: discord.Message, server: Server
) -> None:
    """Show details for a specific cat."""
    logger.info("command: %s", command)
    cat_id = int(command.split(maxsplit=1)[1])
    logger.info("releasing %s", cat_id)
    cat = (
        await Cat.filter(owner__discord_id=message.author.id, id=cat_id)
        .order_by("id")
        .first()
    )
    if not cat:
        await message.add_reaction("❌")
        await message.channel.send(
            f"❌ {message.author.mention}, "
            f"you don't own a cat with id {cat_id}!"
        )
        return
    cat.owner = None
    await cat.save()
    f = BytesIO()
    cat.image.save(f, "PNG")
    f.seek(0)
    return await message.channel.send(
        content=f"👋 You have released **{cat.name}**, "
        f"{message.author.mention}! 👋\n"
        f"{cat.pronouns.he.capitalize()} will be missed.",
        file=discord.File(f, filename="cat.png"),
    )
