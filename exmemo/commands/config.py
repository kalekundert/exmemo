#!/usr/bin/env python3

from . import cli
from .. import Workspace
from pprint import pprint

def config():
    """\
    Dump all the configuration values for the current project.

    Usage:
        exmemo config
    """
    args = cli.parse_args_via_docopt()
    work = Workspace.from_cwd()

    pprint(work.config)





