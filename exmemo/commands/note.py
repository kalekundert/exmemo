#!/usr/bin/env python3

from . import cli
from .. import Workspace

@cli.priority(30)
def new():
    """\
    Create a new experiment with a blank notebook entry.

    Usage:
        exmemo [note] new <title>

    Arguments:
        <title>
            The title of the experiment.  This should be title cased, with 
            words separated by spaces.  Use quotes so the shell won't interpret 
            it as multiple arguments.
    """
    args = cli.parse_args_via_docopt()
    work = Workspace.from_cwd()

    work.init_experiment(args['<title>'])

@cli.priority(30)
def edit():
    """\
    Open the notebook entry for the given experiment in a text editor.

    Usage:
        exmemo [note] edit [<substr>]

    Arguments:
        <substr>
            The experiment to edit.  You don't need to specify the whole name, 
            just enough to be unique.  If multiple experiments match the given 
            substr, you'll will be asked which one you mean.  If you don't 
            specify an experiment, the most recently created one will be used.

    You can specify which text editor you prefer in an `.exmemorc` file, or via 
    the $EDITOR environment variable.
    """
    args = cli.parse_args_via_docopt()
    work = Workspace.from_cwd()
    expt = work.pick_experiment(args['<substr>'])

    work.launch_editor(expt.note_path)

@cli.priority(30)
def open():
    """\
    Open a new terminal cd'd into the given experiment.

    Usage:
        exmemo [note] open [<substr>]

    Arguments:
        <substr>
            The experiment to open.  You don't need to specify the whole name, 
            just enough to be unique.  If multiple experiments match the given 
            substr, you'll will be asked which one you mean.  If you don't 
            specify an experiment, the most recently created one will be used.

    You can specify which terminal you prefer in an `.exmemorc` file, or via 
    the $TERMINAL environment variable.
    """
    args = cli.parse_args_via_docopt()
    work = Workspace.from_cwd()
    expt = work.pick_experiment(args['<substr>'])

    work.launch_terminal(expt.root_dir)

@cli.priority(30)
def directory():
    """\
    Print the path to the given experiment.  This is often used to create an 
    alias that cd's into the given experiment.

    Usage:
        exmemo note directory [<substr>]

    Arguments:
        <substr>
            The experiment you're interested in.  You don't need to specify the 
            whole name, just enough to be unique.  If multiple experiments 
            match the given substr, you'll will be asked which one you mean.  
            If you don't specify an experiment, the most recently created one 
            will be implied.

    Programs are not allowed to change the state of the shell (i.e. to move you 
    into a different directory), so if you want a command that automatically 
    cd's into a given experiment, you need to write your own shell function.  
    This is how such a function would look in bash:

        function ed () {
            d=$(exmemo note directory "$@")
            # Don't try to cd if something goes wrong.
            [ $? = 0 ] && cd $d || echo $d
        }
    """
    args = cli.parse_args_via_docopt()
    work = Workspace.from_cwd()
    expt = work.pick_experiment(args['<substr>'])

    print(expt.root_dir.resolve())

@cli.priority(30)
def rename():
    """\
    Rename 

    Usage:
        exmemo note mv [<substr>] <new_title>
    """
    raise NotImplementedError

@cli.priority(30)
def build():
    """\
    Render the lab notebook to HTML using Sphinx.

    Usage:
        exmemo [note] build [-f]

    Options:
        -f --force
            Force Sphinx to rebuild the whole project from scratch, rather than 
            just building the files that changed since last time.  You often 
            need to do this after you add a new experiment.
    """
    args = cli.parse_args_via_docopt()
    work = Workspace.from_cwd()

    work.build_notebook(args['--force'])

@cli.priority(30)
def browse():
    """
    Open the rendered lab notebook in a web browser.

    Usage:
        exmemo [note] browse [-w]

    Options:
        -w --new-window
            Open a new window in the browser.  The default is to just open a 
            new tab in whichever browser window you most recently used.

    The default browser is firefox, but you can change this by setting either 
    the `browser` configuration option or the `$BROWSER` environment variable.  
    If you plan to use the `-w` option with this command, you may also need to 
    specify the command-line switch used to get the browser to create a new 
    window.  The default is `--new-window`.  That works for both firefox and 
    chrome, but I don't know about other browsers.  You can change it by 
    setting either the `browser_new_window_flag` configuration option or the 
    `$BROWSER_NEW_WINDOW_FLAG` environment variable.
    """
    args = cli.parse_args_via_docopt()
    work = Workspace.from_cwd()
    work.launch_browser(
            f'file://{work.notebook_html_index}',
            args['--new-window']
    )

def ls():
    """\
    Print the names of any existing experiments.

    Usage:
        exmemo note ls [<substr>]

    Arguments:
        <substr>
            Only print the experiments matching the given text.
    """
    args = cli.parse_args_via_docopt()
    workspace = Workspace.from_cwd()

    for expt in workspace.iter_experiments(args['<substr>']):
        print(f'{expt.id:5s} {expt.title}')

