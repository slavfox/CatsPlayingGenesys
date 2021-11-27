# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Application config."""
import logging
import os
from pathlib import Path

import attr
import tomlkit
from cattr.preconf.tomlkit import make_converter

_converter = make_converter()

BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_DIR / "genesys_cats" / "assets"
CONFIG_PATH = os.getenv("CATBOT_CONFIG_PATH", str(BASE_DIR / "config.toml"))


@attr.s(auto_attribs=True)
class Config:
    """Application wide config."""

    discord_token: str
    db_url: str = f"sqlite://{(BASE_DIR / 'db.sqlite3')}"
    log_level: str = "INFO"
    prefix: str = "catbot:"
    cat_activity_chance: float = 0.15
    cat_spawn_chance: float = 0.02
    gm_travel_happening_chance: float = 0.6
    gm_travel_quest_encounter_chance: float = 0.4
    gm_bonus_die_chance: float = 0.2


def load_config() -> Config:
    """Load the config from CONFIG_PATH, or create it if it doesn't exist."""
    if not Path(CONFIG_PATH).is_file():
        c = Config(discord_token="REPLACE THIS")
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            f.write(tomlkit.dumps(_converter.unstructure(c)))
        raise EnvironmentError(
            f"Could not load config file {CONFIG_PATH}. "
            f"It has been created. Edit the discord_token before continuing."
        )
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return _converter.structure(tomlkit.loads(f.read()), Config)


config = load_config()
logging.basicConfig(level=config.log_level)
