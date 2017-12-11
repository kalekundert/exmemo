#!/usr/bin/env python3

from . import cli
from .. import Workspace
from pprint import pprint

def config():
    """\
    Dump all the configuration values for the current project.

    Usage:
        exmemo debug config

    Each project reads configuration information from three different files.  
    Typical paths for a Linux system are given below:

        In-project: /path/to/project/.exmemorc
        User-wide: ~/.config/exmemo/conf.toml
        Site-wide: /etc/xdg/exmemo/conf.toml

    Values in the earlier files take precedence over those in later files.  All 
    three files are TOML (https://github.com/toml-lang/toml).  As of yet there 
    is no definitive list of every configuration option understood by exmemo, 
    but typically the help message for each command will mention any relevant 
    configuration options.
    """
    args = cli.parse_args_via_docopt()
    work = Workspace.from_cwd(strict=False)

    pprint(work.config_paths)
    pprint(work.config)

def readers():
    """\
    Dump all of the protocol reader plugins that exmemo is aware of.

    Usage:
        exmemo debug readers
    """
    from ..readers import get_readers
    pprint(get_readers())

def collectors():
    """\
    Dump all of the data collector plugins that exmemo is aware of.

    Usage:
        exmemo debug collector
    """
    from ..collectors import get_collectors
    pprint(get_collectors())





