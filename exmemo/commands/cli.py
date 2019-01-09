#!/usr/bin/env python3

import sys
import docopt
import textwrap
import functools
from .. import __version__, utils, get_plugins

def run_subcommand(group, name, level=None):
    """
    Run the subcommand with the given group and name.  This is cool because by 
    using `pkg_resources`, other packages can add commands to `exmemo`!
    """
    # Find all the commands that match what the user typed.
    known_subcommands = get_subcommands(group)
    matching_subcommands = [
            x for x in known_subcommands
            if x.name.startswith(name)
    ]

    # If no subcommands match, print an error message and exit.
    if len(matching_subcommands) == 0:
        raise UnknownSubcommand(group, name, known_subcommands)

    # If two or more subcommands match, ask the user which one they meant.
    if len(matching_subcommands) > 1:
        cmd = group.split('.'); del cmd[1]
        i = utils.pick_one(f'{" ".join(cmd)} {x.name}' for x in matching_subcommands)
        matching_subcommands = [matching_subcommands[i]]

    # By this point, there should only be one matching subcommand.
    assert len(matching_subcommands) == 1
    subcommand = matching_subcommands[0]

    # Put the full subcommand name in `sys.argv`, so the argument parser 
    # doesn't need to deal with the extra complexity of partial names.
    level = level or len(group.split('.')) - 1
    sys.argv[level] = subcommand.name

    subcommand()

def run_subcommand_via_docopt(group, level=None, doc=None, command='<command>', **format_args):
    doc = doc or get_caller_docstring()
    briefs = get_subcommand_briefs(group)
    level = level or len(group.split('.')) - 1

    args = docopt.docopt(
            doc=doc.format(subcommands=briefs, **format_args),
            argv=sys.argv[1:level+1],
            version=__version__,
    )

    if args[command]:
        run_subcommand(group, args[command])
        return True

    return False

def parse_args_via_docopt(**format_args):
    doc = get_caller_docstring()
    if format_args:
        doc = doc.format(**format_args)
    return docopt.docopt(doc)

def handle_docopt_help_with_pager(help, version, options, doc):
    """
    Monkey-patched version of `docopt.extras` that uses a pager (less) if the 
    help text is too big to fit on the screen.
    """
    from shutil import get_terminal_size
    from subprocess import run

    if help and any((o.name in ('-h', '--help')) and o.value for o in options):
        doc = doc.strip('\n')
        w, h = get_terminal_size()
        if doc.count('\n') > h: run('less', input=doc, encoding='utf8')
        else: print(doc)
        sys.exit()

    if version and any(o.name == '--version' and o.value for o in options):
        print(version)
        sys.exit()

docopt.extras = handle_docopt_help_with_pager


def get_subcommands(group):
    return get_plugins(group)

def get_subcommand_briefs(group):
    subcommands = get_subcommands(group)

    # Make sure each subcommand has a brief description.

    for subcmd in subcommands:
        if not hasattr(subcmd, 'brief'):

            # Extract a brief description from the docstring.
            subcmd.brief = get_docstring(subcmd).split('.')[0] + '.'

            # Complain if it looks like the docstring extraction didn't work.
            if not subcmd.brief or 'usage:' in subcmd.brief.lower():
                raise ValueError(f"No brief description for '{subcmd.module}.{subcmd.name}'")

    # Sort the subcommands.

    subcommands.sort(key=lambda x: x.lineno)
    subcommands.sort(key=lambda x: x.priority, reverse=True)
    
    # Format the brief descriptions

    sep, indent, padding = ':', 4, 1
    name_width = max(len(x.name) for x in subcommands) + len(sep)
    brief_width = 79 - name_width - indent - padding

    briefs = ""
    for subcmd in subcommands:
        briefs += (
                f"{' ' * indent}"
                f"{subcmd.name + sep:{name_width}s}"
                f"{' ' * padding}"
                f"{textwrap.shorten(subcmd.brief, brief_width)}"
                f"\n"
        )

    return briefs.strip()
    
def get_caller_docstring():
    import inspect
    frame_info = inspect.stack()[2]
    caller = frame_info.frame.f_globals[frame_info.function]
    return get_docstring(caller)

def get_docstring(func):
    return textwrap.dedent(func.__doc__ or '').strip()
    

def main(func):

    @functools.wraps(func)
    def decorator(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except (KeyboardInterrupt, EOFError):
            sys.exit(1)
        except Exception as e:
            if hasattr(e, 'show_message_and_die'):
                print(e.message)
                sys.exit(2)
            else:
                raise

    return decorator


def brief(desc, priority=None):
    def decorator(f):
        f.brief = brief
        if priority is not None:
            f.priority = priority
        return f
    return decorator

def priority(level):
    def decorator(f):
        f.priority = level
        return f
    return decorator


class UnknownSubcommand(Exception):
    show_message_and_die = True
    
    def __init__(self, group, name, known_subcommands):
        cmd = [*group.split('.'), name]; del cmd[1]
        self.message = f"""Unknown command '{" ".join(cmd)}'."""


