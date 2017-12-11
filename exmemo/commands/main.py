#!/usr/bin/env python3

from . import cli

@cli.main
def main():
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

def project():
    """\
    Manage the entire project.

    Usage:
        exmemo project <command> [<args>...]
        exmemo project (-h | --help)
        exmemo project --version

    Commands:
        {subcommands}
    """

    cli.run_subcommand_via_docopt('exmemo.commands.project')

def note():
    """\
    Keep notes on your day-to-day experiments.

    Usage:
        exmemo note <command> [<args>...]
        exmemo note (-h | --help)
        exmemo note --version

    Commands:
        {subcommands}
    """
    cli.run_subcommand_via_docopt('exmemo.commands.note')

def protocol():
    """\
    Manage, display, and print protocols.

    Usage:
        exmemo protocol <command> [<args>...]
        exmemo protocol (-h | --help)
        exmemo protocol --version

    Commands:
        {subcommands}
    """
    cli.run_subcommand_via_docopt('exmemo.commands.protocol')

def data():
    """\
    Interact with data files.

    Usage:
        exmemo data <command> [<args>...]
        exmemo data (-h | --help)
        exmemo data --version

    Commands:
        {subcommands}
    """
    cli.run_subcommand_via_docopt('exmemo.commands.data')

def debug():
    """\
    Print information that can help diagnose problems with exmemo.

    Usage:
        exmemo debug <command> [<args>...]
        exmemo debug (-h | --help)
        exmemo debug --version

    Commands:
        {subcommands}
    """
    cli.run_subcommand_via_docopt('exmemo.commands.debug')

