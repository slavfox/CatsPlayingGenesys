# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Utilities for building text."""
from typing import TYPE_CHECKING, Dict, List, Tuple, Type
from collections import defaultdict

import attr
from inflect import engine

if TYPE_CHECKING:
    from genesys_cats.genesys.datatypes import NPC
    from genesys_cats.models import Cat

p = engine()


@attr.s(auto_attribs=True, slots=True, auto_detect=True, frozen=True)
class Pronouns:
    """Pronouns."""

    he: str
    him: str
    his: str
    himself: str
    plural: bool

    @classmethod
    def from_pronoun_string(cls: Type["Pronouns"], csv: str) -> "Pronouns":
        """
        Build a Pronoun object from a string like "he,him,his,himself,false".
        """
        he, him, his, himself, plural = csv.strip().split(",")
        return cls(
            he=he.strip(),
            him=him.strip(),
            his=his.strip(),
            himself=himself.strip(),
            plural=plural.strip().lower() == "true",
        )

    def to_pronoun_string(self) -> str:
        """Reverse of `from_pronoun_string`"""
        return ",".join(
            [
                self.he,
                self.him,
                self.his,
                self.himself,
                str(self.plural).lower(),
            ]
        )


def replace_pronouns(s: str, pronouns: Pronouns) -> str:
    """Replace template strings with appropriate pronouns."""
    return (
        s.replace("$he$", pronouns.he)
        .replace("$him", pronouns.him)
        .replace("$his$", pronouns.his)
        .replace("$himself$", pronouns.himself)
        .replace("$s$", "" if pronouns.plural else "s")
    )


def capfirst(s: str) -> str:
    """Capitalize the first character of a string."""
    if not s:
        return s
    return s[0].upper() + s[1:]


def describe_cats_list(cats: List["Cat"]) -> str:
    """List the participating cats for an event."""
    if not cats:
        return "The party"
    if len(cats) == 1:
        return str(cats[0])
    return ", ".join(str(cat) for cat in cats[:-1]) + f" and {str(cats[-1])}"


def describe_npcs_list(npcs: List["NPC"]) -> str:
    """Enumerate NPCs in a list."""
    if not npcs:
        return "no one"
    if len(npcs) == 1:
        return str(npcs[0])

    npc_counts: Dict[Tuple[str, bool], int] = defaultdict(int)

    for npc in npcs:
        npc_counts[(npc.name, npc.generic)] += 1

    npc_strs = []

    for (name, generic), count in sorted(
        npc_counts.items(), key=lambda i: i[1], reverse=True
    ):
        if count == 1:
            if generic:
                npc_strs.append(f"{p.a(name)}")
            else:
                npc_strs.append(name)
        else:
            if generic:
                npc_strs.append(f"{p.plural(name, count)}")
            else:
                for _ in range(count):
                    npc_strs.append(name)

    if len(npc_strs) == 1:
        return npc_strs[0]

    return ", ".join(npc_strs[:-1]) + f" and {npc_strs[-1]}"
