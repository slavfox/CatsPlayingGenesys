# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Serialization/deserialization utilities for RPG state."""
from typing import Any, Dict

from cattr import GenConverter
from cattr.preconf.bson import make_converter

from genesys_cats.genesys.core import Event, Quest, event_types, quest_types

converter: GenConverter = make_converter()


def unstructure_event(o: Event) -> Dict[str, Any]:
    """Unstructure an Event into a dictionary."""
    return {
        "_t": o.__class__.__name__,
        **converter.unstructure_attrs_asdict(o),
    }


def structure_event(obj: Dict[str, Any], _: Any):
    """Structure a dictionary back into an Event."""
    event_type = obj.pop("_t")
    return converter.structure_attrs_fromdict(obj, event_types[event_type])


def unstructure_quest(o: Quest) -> Dict[str, Any]:
    """Unstructure a Quest into a dictionary."""
    return {
        "_t": o.__class__.__name__,
        **converter.unstructure_attrs_asdict(o),
    }


def structure_quest(obj: Dict[str, Any], _: Any):
    """Structure a dictionary back into a Quest."""
    event_type = obj.pop("_t")
    return converter.structure_attrs_fromdict(obj, quest_types[event_type])


converter.register_structure_hook(Event, structure_event)
converter.register_structure_hook(Quest, structure_quest)
converter.register_unstructure_hook(Event, unstructure_event)
converter.register_unstructure_hook(Quest, unstructure_quest)

# pylint: disable=unused-import,wrong-import-position
from genesys_cats.genesys.gm.combat import Combat  # noqa

# Import all Event subclasses here to ensure they all get registered
# pylint: disable=unused-import,wrong-import-position
from genesys_cats.genesys.gm.travel import Travel  # noqa
