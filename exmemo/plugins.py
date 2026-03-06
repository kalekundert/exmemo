#!/usr/bin/env python3

import inspect
from importlib.metadata import entry_points

def get_plugins(group):
    plugins = []
    already_seen = set()

    for entry_point in entry_points(group=group):

        # Every entry point appears to generated twice.  I couldn't easily 
        # figure out the root cause for this, so here I'm just treating the 
        # symptom.
        if entry_point.value in already_seen:
            continue
        else:
            already_seen.add(entry_point.value)

        plugin = entry_point.load()
        plugin.name = entry_point.name
        plugin.module = entry_point.module
        plugin.lineno = inspect.getsourcelines(plugin)[1]
        plugin.priority = getattr(plugin, 'priority', 0)
        plugins.append(plugin)

    plugins.sort(key=lambda x: x.lineno)
    plugins.sort(key=lambda x: x.priority, reverse=True)

    return plugins
