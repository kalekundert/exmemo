#!/usr/bin/env python3

# I wrote this module with the intention of being able to break it out into 
# it's own thing.

import sys
import docopt
import textwrap
import functools

from .. import __version__
from pkg_resources import iter_entry_points, DistributionNotFound
from typing import NamedTuple
from pprint import pprint

def one(iterable, too_short=None, too_long=None):
    """Return the only element from the iterable.

    Raise an exception if the iterable is empty or longer than 1 element. For
    example, assert that a DB query returns a single, unique result.

        >>> one(['val'])
        'val'

        >>> one(['val', 'other'])  # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
        ...
        ValueError: too many values to unpack (expected 1)

        >>> one([])  # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
        ...
        ValueError: not enough values to unpack (expected 1, got 0)

    By default, ``one()`` will raise a ValueError if the iterable has the wrong 
    number of elements.  However, you can also provide custom exceptions via 
    the ``too_short`` and ``too_long`` arguments to raise if the iterable is 
    either too short (i.e. empty) or too long (i.e. more than one element).
    
    ``one()`` attempts to advance the iterable twice in order to ensure there
    aren't further items. Because this discards any second item, ``one()`` is
    not suitable in situations where you want to catch its exception and then
    try an alternative treatment of the iterable. It should be used only when a
    iterable longer than 1 item is, in fact, an error.

    """
    it = iter(iterable)

    try:
        value = next(it)
    except StopIteration:
        raise too_short or ValueError("not enough values to unpack (expected 1, got 0)") from None

    try:
        next(it)
    except StopIteration:
        pass
    else:
        raise too_long or ValueError("too many values to unpack (expected 1)") from None

    return value


def run_subcommand(group, subcommand):
    # Load every `exmemo` command installed on this system.  This is cool 
    # because by using `pkg_resources`, other packages can add commands to 
    # `exmemo`!
    
    entry_point = one(
            iter_entry_points(group=group, name=subcommand),
            UnknownSubcommand(group, subcommand),
            OverspecifiedSubcommand(group, subcommand),
    )
    try:
        entry_point.require()
    except DistributionNotFound as error:
        raise MissingDependency(subcommand, error)

    subcommand = main(entry_point.load())
    subcommand()

def run_subcommand_via_docopt(group, level=None, doc=None, command='<command>'):
    doc = doc or get_caller_docstring()
    briefs = get_subcommand_briefs(group)
    level = level or len(group.split('.')) - 1

    args = docopt.docopt(
            doc=doc.format(subcommands=briefs),
            argv=sys.argv[1:level+1],
            version=__version__,
    )

    if args[command]:
        run_subcommand(group, args[command])
        return True

    return False

def parse_args_via_docopt():
    doc = get_caller_docstring()
    return docopt.docopt(doc)

def get_subcommand_briefs(group):
    entry_points = {
            x.name: x.load()
            for x in iter_entry_points(group=group)
    }

    brief_infos = []

    class BriefInfo(NamedTuple): #
        subcommand: str
        brief_desc: str
        importance: int

    for entry_point in iter_entry_points(group=group):
        subcommand = entry_point.name
        func = entry_point.load()

        # Check if the function has an explicit brief message, otherwise use 
        # the first sentence from its docstring.

        try:
            brief_desc = func.brief
        except AttributeError:
            brief_desc = get_docstring(func).split('.')[0] + '.'

        if 'usage:' in brief_desc.lower():
            pprint(dir(func))
            raise ValueError(f"No brief description for '{func.__module__}.{func.__name__}'")

        # Check if the function specifies what order that it should be listed 
        # in.  If not, it'll be listed alphabetically.

        try:
            importance = func.importance
        except AttributeError:
            importance = 0

        info = BriefInfo(subcommand, brief_desc, importance)
        brief_infos.append(info)

    # Sort the brief descriptions

    brief_infos.sort(key=lambda x: x.subcommand)
    brief_infos.sort(key=lambda x: x.importance)
    
    # Format the brief descriptions

    sep = ':'
    subcmd_width = max(len(x.subcommand) for x in brief_infos) + len(sep)
    indent, padding = 4, 1
    desc_width = 79 - subcmd_width - indent - padding

    briefs = ""
    for info in brief_infos:
        briefs += (
                f"{' ' * indent}"
                f"{info.subcommand + sep:{subcmd_width}s}"
                f"{' ' * padding}"
                f"{textwrap.shorten(info.brief_desc, desc_width)}"
                f"\n"
        )

    return briefs.strip()
    
def get_caller_docstring():
    import inspect
    frame_info = inspect.stack()[2]
    caller = frame_info.frame.f_globals[frame_info.function]
    return get_docstring(caller)

def get_docstring(func):
    return textwrap.dedent(func.__doc__).strip()
    

def main(func):

    @functools.wraps(func)
    def decorator(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except (KeyboardInterrupt, EOFError):
            sys.exit()
        except Exception as e:
            if hasattr(e, 'show_message_and_die'):
                print(e.message)
                sys.exit()
            else:
                raise

    return decorator


def brief(desc, importance=None):
    def decorator(f):
        f.brief = brief
        if importance is not None:
            f.importance = importance
        return f
    return decorator

def importance(level):
    def decorator(f):
        f.importance = level
        return f
    return decorator


class UnknownSubcommand(Exception):
    
    def __init__(self, group, subcommand):
        self.group = group
        self.subcommand = subcommand


class OverspecifiedSubcommand(Exception):
    
    def __init__(self, group, subcommand):
        self.group = group
        self.subcommand = subcommand


class MissingDependency(Exception):
    
    def __init__(self, group, error):
        self.group = group
        self.error = error


