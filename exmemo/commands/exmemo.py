#!/usr/bin/env python3

from . import cli

@cli.main
def exmemo():
    """\
    Manage a project directory.

    Usage:
        exmemo <command> [<args>...]
        exmemo (-h | --help)
        exmemo --version

    Commands:
        {subcommands}
    """

    # Hmm, if I give `exmemo project -h`, it won't match any of the above usage 
    # strings, so docopt will terminate and show me the usage hint for this 
    # command.  That's not what I want...

    cli.run_subcommand_via_docopt('exmemo.commands')
