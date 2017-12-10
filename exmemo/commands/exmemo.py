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
    cli.run_subcommand_via_docopt('exmemo.commands')

