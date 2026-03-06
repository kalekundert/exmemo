#!/usr/bin/env python3

from . import cli
from .. import Workspace, Experiment, ExperimentNotFound, iter_experiments

from math import inf
from pathlib import Path

# If no experiments specified:
# - show all experiments with matching statuses
#
# If experiments specified:
# - show all specified experiments regardless of status

@cli.priority(30)
def status():
    """\
    Show which experiments are currently ready/in progress/complete/etc.

    Usage:
        exmemo [note] status [<expt>...] [-nrpbca] [-RA]

    Arguments:
        <expt>
            Which experiments to show statuses for.  If no experiments are 
            specified, the default is to show all experiments that have the 
            specified statuses, or "ready" and "in progress" if no statuses are 
            specified.  If one or more experiments are specified but no 
            statuses are, all the specified experiments will be shown.

            If no experiments are specified, think of this command as providing 
            an overview of the whole project.  By default, it will display all 
            experiments that are either "ready" or "in progress".  If one or 
            more experiments are specified, think of this command as 

    Options:
        -n --new
            Show new experiments.  This is the default status that all 
            experiments start with.

        -r --ready
            Show experiments that are ready to start (i.e. fully planned, all 
            materials available, etc.).

        -p --in-progress
            Show experiments that are currently in progress (i.e. data still 
            being collected or analyzed).

        -b --blocked
            Show experiments that are waiting for other experiments to 
            complete.

        -c --complete
            Show experiments that have been completed.

        -a --abandoned
            Show experiments that have been abandoned (i.e. that you are not 
            planning to complete in the immediate future).

        -A --all
            Show all experiments, regardless of their status.  This is 
            equivalent to `-nrpbca`.

        -R --recursive
            Include any descendants of the specified experiments.

    Experiments typically advance from "new" to "ready" to "in progress" to 
    "complete".  Experiments may be "abandoned" at any point in this pipeline, 
    and are considered "blocked" if they have prerequisite experiments that are 
    not either "complete" or "abandoned".

    The default (if no experiments are specified) is to show all "ready" and 
    "in progress" experiments.

    By default, all "ready" and "in progress" experiments will be shown.  You 
    should try to keep only a handful of experiments in these categories at any 
    one time.  If there are too many, it may be a sign that your concentration 
    is split in too many directions.  Consider temporarily "abandoning" any 
    experiments that you do not have immediate plans to complete, in order to 
    focus your attention on those that you do.
    """
    args = cli.parse_args_via_docopt()
    work = Workspace.from_cwd()

    def iter_selected_experiments():
        if not args['<expt>']:
            yield from work.iter_experiments()
        else:
            for dir in args['<expt>']:
                dir = Path(dir)
                if not dir.is_dir():
                    continue

                # If the given directory is an experiment, yield it.
                try:
                    yield Experiment.from_dir(dir, work)
                except ExperimentNotFound:
                    pass
                else:
                    if not args['--recursive']:
                        return

                # Yield all experiments contained in the given directory.
                yield from iter_experiments(
                        work, dir,
                        recursive=args['--recursive'],
                )

    expts = {}
    for expt in iter_selected_experiments():
        expts.setdefault(expt.status, set()).add(expt)

    status_flags = {
            'new': '--new',
            'ready': '--ready',
            'in progress': '--in-progress',
            'complete': '--complete',
            'abandoned': '--abandoned',
            'blocked': '--blocked',
    }
    status_toggles = {
            k: args[status_flags[k]] or args['--all']
            for k in status_flags
    }

    if not any(status_toggles.values()):
        if args['<expt>']:
            status_toggles = {k: True for k in status_toggles}
        else:
            status_toggles['ready'] = True
            status_toggles['in progress'] = True

    def by_id(x):
        return x.id or inf

    for status, toggle in status_toggles.items():
        if not toggle:
            continue
        if status not in expts:
            continue

        print(status.upper())

        for expt in sorted(expts.get(status, []), key=by_id):
            print(f'{expt.id or "?":<5} {expt.root_dir_rel}')

            if status == 'blocked':
                print('      blocked by: ' + ','.join(map(str, expt.blocking_prereq_ids)))

        print()

@cli.priority(30)
def update():
    """\
    Change the status (e.g. ready, in progress, complete, etc.) of the given
    experiment.

    Usage:
        exmemo [note] update [<id_or_substr>] 
            (-n | -r | -p | -c | -a | -b <id> | -B <id>)

    Arguments:
        <id_or_substr>
            The experiment to update.  If not specified, the current working 
            directory will be used (if it is in fact an experiment).

    Options:
        -n --new
            Mark the experiment as new.

        -r --ready
            Mark the experiment as ready.

        -p --in-progress
            Mark the experiment as in progress.

        -b --blocked-by <id_or_substr>
            Mark the experiment as blocked by the experiment identified by the 
            given id/tag.  It is an error to specify an non-unique tag.

        -B --not-blocked-by <id_or_substr>
            Mark the experiment as *not* blocked by the experiment identified 
            by the given id/tag.  It is an error to specify an non-unique tag.

        -c --complete
            Mark the experiment as complete.

        -a --abandoned
            Mark the experiment as abandoned.
            Show experiments that have been abandoned (i.e. that you are not 
            planning to complete in the immediate future).
    
    See `exmemo note status -h` for more information on each status.
    """
    args = cli.parse_args_via_docopt()
    work = Workspace.from_cwd()
    expt = work.pick_experiment(args['<id_or_substr>'])

    if args['--new']:
        expt.status = 'new'

    if args['--ready']:
        expt.status = 'ready'

    if args['--in-progress']:
        expt.status = 'in progress'

    if b := args['--blocked-by']:
        expt.prereqs.add(work.pick_experiment(b))
        print(f"Prerequisites: {', '.join(sorted(expt.prereq_ids))}")

    if b := args['--not-blocked-by']:
        expt.prereqs.discard(work.pick_experiment(b))
        print(f"Prerequisites: {', '.join(sorted(expt.prereq_ids))}")

    if args['--complete']:
        expt.status = 'complete'

    if args['--abandoned']:
        expt.status = 'abandoned'

    if expt.id:
        print(f"Set experiment #{expt.id} status to: {expt.status.upper()}")
    else:
        print(f"Set experiment status to: {expt.status.upper()}")

@cli.priority(30)
def find():
    """\
    Find the notebook entry with the given id/tag.

    Usage:
        exmemo [note] edit [<id_or_substr>]

    Arguments:
        <substr>
            The experiment to find.  You can specify either an id number of a 
            partial name (enough to be unique).
    """
    args = cli.parse_args_via_docopt()
    work = Workspace.from_cwd()
    expt = work.pick_experiment(args['<id_or_substr>'])

    print(f'{expt.id or "?":<5} {expt.root_dir_rel}')

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
        exmemo note ls
    """
    args = cli.parse_args_via_docopt()
    work = Workspace.from_cwd()
    expts = sorted(work.iter_experiments(), key=lambda x: x.id or inf)

    for expt in expts:
        print(f'{expt.id or "?":<5} {expt.root_dir_rel}')



def serve():
    """\
    Launch a web-server for the current workspace.

    Usage:
        exmemo note serve
    """
    from exmemo.webserver import create_app, refresh_sphinx

    work = Workspace.from_cwd()

    app = create_app(work)
    app.run(debug=True)

def refresh():
    """
    Regenerate the cache files used by the web server.

    Usage:
        exmemo note refresh
    """
    from exmemo.webserver import refresh_sphinx
    work = Workspace.from_cwd()
    refresh_sphinx(work)
