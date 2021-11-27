# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Runnable entry point for the bot."""
from tortoise import run_async

from genesys_cats.bot.discord_bot import CatBot
from genesys_cats.config import config

if __name__ == "__main__":
    bot = CatBot()
    run_async(bot.start(config.discord_token))
