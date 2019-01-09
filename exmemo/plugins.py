#!/usr/bin/env python3

import inspect
from pkg_resources import iter_entry_points

def get_plugins(group):
    plugins = []

    for entry_point in iter_entry_points(group=group):
        plugin = entry_point.load()
        plugin.name = entry_point.name
        plugin.module = entry_point.module_name
        plugin.lineno = inspect.getsourcelines(plugin)[1]
        plugin.priority = getattr(plugin, 'priority', 0)
        plugins.append(plugin)

    plugins.sort(key=lambda x: x.lineno)
    plugins.sort(key=lambda x: x.priority, reverse=True)

    return plugins
