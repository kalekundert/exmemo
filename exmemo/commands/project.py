#!/usr/bin/env python3

import docopt
from . import cli
from .. import Workspace
from pprint import pprint

def project():
    """\
    What the fuck.

    Usage:
        exmemo project <command> [<args>...]
        exmemo project (-h | --help)
        exmemo project --version

    Commands:
        {subcommands}
    """

    cli.run_subcommand_via_docopt('exmemo.commands.project')

def init():
    """\
    Create a directory layout for a new project.  This layout will include 
    directories for data files, analysis scripts, protocols, notebook entries, 
    and documents.

    Usage:
        exmemo [project] init <slug>
    """

    args = cli.parse_args_via_docopt()
    work = Workspace(args['<slug>'])

    work.init_dirs()

def root():
    """
    Print the root directory of the project.

    Usage:
        exmemo project root
    """
    args = cli.parse_args_via_docopt()
    work = Workspace.from_cwd()
    print
    pprint(args)


