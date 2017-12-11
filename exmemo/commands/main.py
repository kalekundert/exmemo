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

def expt():
    """\
    Keep notes on your day-to-day experiments.

    Usage:
        exmemo expt <command> [<args>...]
        exmemo expt (-h | --help)
        exmemo expt --version

    Commands:
        {subcommands}
    """
    cli.run_subcommand_via_docopt('exmemo.commands.expt')

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

