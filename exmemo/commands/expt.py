#!/usr/bin/env python3

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
    args = cli.parse_args_via_docopt()
    workspace = Workspace.from_cwd()

    for expt in workspace.yield_experiments(args['<slug>']):
        print(expt.name)

def new():
    """\
    Create a new experiment with a blank notebook entry.

    Usage:
        exmemo expt new <title>

    Arguments:
        <title>
            The title of the experiment.  This should be title cased, with 
            words separated by spaces.  Use quotes so the shell won't interpret 
            it as multiple arguments.
    """
    args = cli.parse_args_via_docopt()
    work = Workspace.from_cwd()

    work.init_experiment(args['<title>'])

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
    args = cli.parse_args_via_docopt()
    work = Workspace.from_cwd()
    expt = work.pick_experiment(args['<slug>'])
    path = work.get_notebook_entry(expt)

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
    args = cli.parse_args_via_docopt()
    work = Workspace.from_cwd()
    expt = work.pick_experiment(args['<slug>'])

    work.launch_terminal(expt)

