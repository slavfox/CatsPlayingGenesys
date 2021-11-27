# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""The Discord bot itself."""
import random
from typing import Optional
from logging import getLogger

import discord

from genesys_cats.bot.commands import handle_command
from genesys_cats.bot.helpers import get_server, send_cat, spawn_new_cat
from genesys_cats.config import config
from genesys_cats.genesys.core import GameState
from genesys_cats.genesys.gm.travel import Travel
from genesys_cats.genesys.serde import converter
from genesys_cats.models import Cat, Server, init_db

logger = getLogger("discord_bot")


class CatBot(discord.Client):
    """The actual Discord bot."""

    async def on_ready(self):
        """Initialize the bot on connection."""
        await init_db()
        await self.change_presence(activity=discord.Game("catbot: help"))
        logger.info("Bot ready!")

    async def on_message(self, message: discord.Message) -> None:
        """A message was sent in the server."""
        if message.author == self.user:
            return
        if message.content.lower().startswith("catbot:"):
            # It's a command
            logger.debug("Got a command")
            try:
                await handle_command(self, message)
                return
            except Exception as e:
                logger.exception(e)
                raise e

        server_obj = await get_server(message)
        if not server_obj:
            return

        if (
            server_obj.cat_channel_id is None
            or server_obj.command_channel_id is None
        ):
            return

        if random.random() < config.cat_activity_chance:
            await self.play_genesys(server_obj, message)

        if random.random() < config.cat_spawn_chance:
            author_cats = await Cat.filter(owner__discord_id=message.author.id)

            if author_cats:
                invited_by: Optional[Cat] = random.choice(author_cats)
            else:
                invited_by = None

            await send_cat(
                self.get_channel(server_obj.cat_channel_id),
                *await spawn_new_cat(server_obj, invited_by=invited_by)
            )

    async def play_genesys(
        self, server: Server, message: discord.Message
    ) -> None:
        """Get an update for cats playing RPGs."""
        last_authors = [
            message.author.id
            async for message in message.channel.history(limit=5)
        ]
        cats = await Cat.filter(owner__discord_id__in=last_authors)
        if not cats:
            return
        try:
            state = converter.structure(server.genesys_state, GameState)
        except (KeyError, AttributeError, TypeError) as err:
            logger.critical("Couldn't load state: %s", err)
            state = GameState(current_event=Travel())
        try:
            message = state.current_event.generate_update(state, cats)
        except Exception as e:
            logger.exception(e)
            raise e
        server.genesys_state = converter.unstructure(state)
        await server.save()
        await message.send(self.get_channel(server.cat_channel_id))
        return
