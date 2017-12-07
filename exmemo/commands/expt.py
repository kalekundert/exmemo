#!/usr/bin/env python3

import docopt
from . import cli
from .. import Workspace
from pprint import pprint

def expt():
    """\
    Keep notes on your day-to-day experiments.

    Usage:
        exmemo expt <command> [<args>...]

    Commands:
        {subcommands}
    """
    cli.run_subcommand_via_docopt('exmemo.commands.expt', 2)

def ls():
    """\
    Print the names of any existing experiments.

    Usage:
        exmemo expt ls [<slug>]

    Arguments:
        <slug>
            Only print the experiments matching the given text.
    """
    args = docopt.docopt(ls.__doc__)
    workspace = Workspace.from_cwd()

    for expt in workspace.yield_experiments(args['<slug>']):
        print(expt.name)

def edit():
    """\
    Open the notebook entry for the given experiment in a text editor.

    Usage:
        exmemo expt edit [<slug>]

    Arguments:
        <slug>
            The experiment to edit.  You don't need to specify the whole name, 
            just enough to be unique.  If multiple experiments match the given 
            slug, you'll will be asked which one you mean.  If you don't 
            specify an experiment, the most recently created one will be used.

    You can specify which text editor you prefer in an `.exmemorc` file, or via 
    the $EDITOR environment variable.
    """
    args = docopt.docopt(edit.__doc__)
    work = Workspace.from_cwd()
    expt = work.pick_experiment(args['<slug>'])
    path = expt / f'{expt.name[9:]}.rst'

    work.launch_editor(path)

def open():
    """\
    Open a new terminal cd'd into the given experiment.

    Usage:
        exmemo expt open [<slug>]

    Arguments:
        <slug>
            The experiment to open.  You don't need to specify the whole name, 
            just enough to be unique.  If multiple experiments match the given 
            slug, you'll will be asked which one you mean.  If you don't 
            specify an experiment, the most recently created one will be used.

    You can specify which terminal you prefer in an `.exmemorc` file, or via 
    the $TERMINAL environment variable.
    """
    args = docopt.docopt(open.__doc__)
    work = Workspace.from_cwd()
    expt = work.pick_experiment(args['<slug>'])

    work.launch_terminal(expt)

