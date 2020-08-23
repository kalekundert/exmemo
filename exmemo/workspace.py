#!/usr/bin/env python3

import os
import sys
import platform
import toml
import formic
import shlex
import subprocess
import collections
from subprocess import DEVNULL
from datetime import datetime
from pathlib import Path
from appdirs import AppDirs
from more_itertools import one
from . import utils
from .errors import *

app = AppDirs('exmemo')

class Workspace:

    @classmethod
    def from_dir(cls, dir, strict=True):
        """
        Create a workspace object containing given directory (or the current 
        working directory, by default).  This involves descending the directory 
        hierarchy looking for the root of the project, which should contain a 
        characteristic set of files and directories.
        """

        dir = given_dir = Path(dir).resolve()
        work = given_work = Workspace(dir)

        while not work.has_project_files:
            dir = dir.parent
            if dir == Path('/'):
                if strict: raise WorkspaceNotFound(given_dir)
                else: return given_work
            else:
                work = Workspace(dir)

        return work

    @classmethod
    def from_path(cls, path, strict=True):
        """
        Create a workspace object containing given path.  This involves 
        descending the directory hierarchy looking for the root of the project, 
        which should contain a characteristic set of files and directories.
        """
        path = Path(path)
        dir = path if path.is_dir() else path.parent
        return cls.from_dir(dir, strict)

    @classmethod
    def from_cwd(cls, strict=True):
        """
        Create a workspace object containing given directory (or the current 
        working directory, by default).  This involves descending the directory 
        hierarchy looking for the root of the project, which should contain a 
        characteristic set of files and directories.
        """
        return cls.from_dir(cls.get_cwd(), strict)

    @classmethod
    def from_sphinx_env(cls, env):
        return cls.from_path(env.doc2path(env.docname))

    @staticmethod
    def get_cwd():
        """
        Return the current working directory, making an effort to keep the path 
        nice and short by not resolving symlinks.
        """
        # Most shells will set `$PWD` with the path the user sees the current 
        # working directory as, taking into account whichever symlinks they 
        # used to get there.  So this is the path we want to use, if it's 
        # available.  If it's not, fall back on `os.getcwd()`, which will give 
        # us the current working directory without any symlinks.

        # The logic is really complicated because I ran into a bug in xonsh 
        # where `os.getenv('PWD')` and `os.getcwd()` would actually return 
        # different paths!  To be robust against this kind of situation, the 
        # code now checks if the two paths differ and trusts `os.getcwd()` if 
        # they do.

        pretty_cwd = os.getenv('PWD')
        real_cwd = os.getcwd()

        if not pretty_cwd:
            return Path(real_cwd)
        if not os.path.samefile(pretty_cwd, real_cwd):
            return Path(real_cwd)

        return Path(pretty_cwd)


    def __init__(self, root):
        self._root = Path(root).resolve()

        if not self.config_paths:
            self._config = {}
        else:
            self._config = toml.load([str(x) for x in self.config_paths])

    @property
    def root_dir(self):
        return self._root

    @property
    def config(self):
        return self._config

    @property
    def config_paths(self):
        paths = [self.site_config_path, self.user_config_path, self.rcfile]
        return [x for x in paths if x.exists()]

    @property
    def site_config_path(self):
        return Path(app.site_config_dir) / 'conf.toml'

    @property
    def user_config_path(self):
        return Path(app.user_config_dir) / 'conf.toml'

    @property
    def project_config_path(self):
        return self.root_dir / '.exmemorc'

    rcfile = project_config_path

    @property
    def analysis_dir(self):
        return self.root_dir / 'analysis'

    @property
    def data_dir(self):
        return self.root_dir / 'data'

    @property
    def documents_dir(self):
        return self.root_dir / 'documents'

    @property
    def notebook_dir(self):
        return self.root_dir / 'notebook'

    @property
    def notebook_html_index(self):
        return self.notebook_dir / 'build' / 'html' / 'index.html'

    @property
    def has_project_files(self):
        if not self.rcfile.exists():
            return False
        if not self.analysis_dir.exists():
            return False
        if not self.data_dir.exists():
            return False
        if not self.documents_dir.exists():
            return False
        if not self.notebook_dir.exists():
            return False
        return True

    def init_project(self, title):
        from cookiecutter.main import cookiecutter
        from .cookiecutter import cookiecutter_path
        from click.exceptions import Abort

        url = self.config.get('cookiecutter_url') or cookiecutter_path

        try:
            cookiecutter(str(url), extra_context={
                    'project_title': title,
                    'year': datetime.today().year,
            })
        except Abort:
            raise KeyboardInterrupt

    def init_experiment(self, title):
        slug = slug_from_title(title)
        expt = self.notebook_dir / f'{utils.ymd()}_{slug}'
        rst = expt / f'{slug}.rst'

        if not os.path.isdir(expt):
            expt.mkdir()
        else:
            sys.exit('Experiment exists. Use exmemo [note] edit [<substr>].')

        with rst.open('w') as file:
            file.write(f"""\
{'*' * len(title)}
{title}
{'*' * len(title)}
""")
        self.launch_editor(rst)

    def iter_experiments(self, recursive=True):
        yield from iter_experiments(
                self,
                self.notebook_dir,
                recursive=recursive,
        )

    def iter_experiments_toc(self):
        yield from iter_experiments(self, self.notebook_dir, recursive=False)

    def find_experiment(self, id):
        return one(
                (x for x in self.iter_experiments() if x.id == id),
                too_short=ExperimentNotFound(id),
                too_long=IntegrityError(f"multiple experiments with id #{id}---this should never happen and must be repaired manually"),
        )

    def pick_experiment(self, tag=None):
        try:
            id = int(tag)

        except ValueError:
            cwd_expt = Experiment(self, os.getcwd())
            no_default = None if cwd_expt.check_paths() else UserError("must specify an experiment")

            return pick_via_tag(
                tag,
                self.iter_experiments(),
                get_path=lambda x: x.root_dir_rel,
                get_extra_score=lambda x: x.id,
                default=cwd_expt,
                no_default=no_default,
                no_matches=UserError(f"no experiments matching '{tag}'"),
            )

        else:
            return self.find_experiment(id)

    def assign_experiment_ids(self):
        next_id = max(
                (x.id for x in self.iter_experiments() if x.id is not None),
                default=1
        )

        expts = {True: [], False: []}
        for expt in self.iter_experiments():
            expts[expt.id is not None].append(expt)

        next_id = max((x.id for x in expts[True]), default=0) + 1
        expts[False].sort(key=lambda x: os.path.getmtime(x.root_dir))

        for new_expt in expts[False]:
            new_expt.assign_id(next_id)
            next_id += 1

    def iter_data(self, substr=None):
        return iter_paths_matching_substr(self.data_dir, substr)

    def pick_data(self, tag):
        return pick_via_tag(
            tag,
            self.iter_data(),
            get_path=lambda x: x.relative_to(self.data_dir),
            default=cwd_expt,
            no_matches=UserError(f"no data files matching '{tag}'"),
        )

        return self.pick_path(
                substr, self.iter_data(substr),
                no_choices=CantMatchSubstr('data files', substr),
        )

    def launch_editor(self, path):
        if platform.system() == 'Windows':
            system_editor = 'write.exe'
        else:
            system_editor = 'vim'

        editor = self.config.get('editor', os.environ.get('EDITOR', system_editor))
        cmd = *shlex.split(editor), str(path)
        subprocess.Popen(cmd)

    def launch_terminal(self, dir):
        term = self.config.get('terminal', os.environ.get('TERMINAL')) or 'xterm'
        cmd = shlex.split(term)
        subprocess.Popen(cmd, cwd=dir, stdout=DEVNULL, stderr=DEVNULL)

    def launch_pdf(self, path):
        pdf = self.config.get('pdf', os.environ.get('PDF')) or 'evince'
        cmd = *shlex.split(pdf), str(path)
        subprocess.Popen(cmd)

    def launch_browser(self, url, new_window=False):
        browser = self.config.get('browser', os.environ.get('BROWSER')) or 'firefox'
        new_window_flag = self.config.get('browser_new_window_flag', os.environ.get('BROWSER_NEW_WINDOW_FLAG')) or '--new-window'

        if new_window:
            cmd = *shlex.split(browser), *shlex.split(new_window_flag), str(url)
        else:
            cmd = *shlex.split(browser), str(url)

        subprocess.Popen(cmd)

    def sync_data(self, verbose):
        from . import collectors
        collectors.sync_data(self, verbose)

    def build_notebook(self, force=False):
        if force:
            make = 'make', 'clean', 'html'
        else:
            make = 'make', 'html'

        subprocess.run(make, cwd=self.notebook_dir)

    def get_data_collectors():
        pass


class Experiment:
    """
    A directory containing all the information relevant to a single experiment, 
    e.g. notes, data files, scripts, etc.
    
    In order to be considered as experiment
    A directory is an experiment directory if the following criteria are 
    satisfied:

    - Subdirectory of notebook/
    - Contains a `notes.txt` file
    """

    @classmethod
    def from_dir(cls, dir, work=None, strict=True):
        if work is None:
            work = Workspace.from_dir(dir)

        expt = Experiment(work, dir)

        if strict and not expt.check_paths():
            raise ExperimentNotFound(dir)

        return expt

    @classmethod
    def from_sphinx_env(cls, env, work=None, strict=True):
        doc_path = Path(env.doc2path(env.docname))
        return cls.from_dir(doc_path.parent, work=None, strict=strict)


    def __init__(self, work, root):
        self._work = work
        self._root = Path(root).resolve()
        self._id_path = self._root / '.id'
        self._note_path = self._root / 'notes.rst'

    def __repr__(self):
        rel_dir = self.root_dir.relative_to(self.workspace.notebook_dir)
        return f"{self.__class__.__qualname__}(root='{rel_dir}')"

    @property
    def workspace(self):
        return self._work

    @property
    def root_dir(self):
        return self._root

    @property
    def root_dir_rel(self):
        return self._root.relative_to(self._work.notebook_dir)

    @property
    def note_path(self):
        return self._note_path

    @property
    def id(self):
        try:
            return int(self._id_path.read_text())
        except (NotADirectoryError, FileNotFoundError):
            return None

    @property
    def parent(self):
        return self.get_ancestor(1)

    @property
    def title(self):
        notes = self.note_path.read_text()
        return notes.splitlines()[1]

    def check_paths(self):
        return self.note_path.exists() and any(
                self.workspace.notebook_dir.samefile(x)
                for x in self.root_dir.parents
        )

    def assign_id(self, id):
        if self.id is not None:
            raise IntegrityError(f"can't assign id #{id} to experiment #{self.id}")

        self._id_path.write_text(str(id))

    def get_ancestor(self, level=1):
        parent = self.from_dir(self.root_dir.parent, work=self.workspace)

        if level == 1:
            return parent
        elif level > 1:
            return parent.get_ancestor(level - 1)
        else:
            raise UserError(f"level must be ≥ 1, not {level}")

    def iter_experiments(self):
        yield from iter_experiments(
                self.workspace,
                self.root_dir,
                recursive=True,
        )

    def iter_experiments_toc(self):
        yield from iter_experiments(
                self.workspace,
                self.root_dir,
                recursive=False,
        )

# These exceptions are a mess:
# - Don't inherit from a common class
# - Too fine-grained
# - Don't set message in superclass


def pick_via_tag(
        tag,
        choices,
        get_path=None,
        get_extra_score=None,
        default=None,
        no_matches=None,
        no_default=None
    ):
    # This function should maybe be factored out into it's own library.  I'm 
    # not crazy about adding stepwise as a dependency.
    from stepwise.library import _match_tag as match_tag

    # Allow choices to be an iterator.
    choices = list(choices)

    if not choices:
        if no_default:
            raise no_default
        else:
            return default

    scores = []

    for choice in choices:
        path = get_path(choice)
        score = match_tag(tag, path)
        extra_score = get_extra_score(choice) if get_extra_score else None

        if score:
            scores.append((score, extra_score, choice))

    matches = [x[2] for x in sorted(scores)]

    if not matches:
        raise no_matches or UserError(f"no matches for '{tag}'")

    if len(matches) == 1:
        return matches[0]
    else:
        # There should be a config setting to change how this works (i.e. CLI 
        # vs GUI vs automatic choice).
        return pick_one_via_cli(matches, get_path)

def pick_one_via_cli(choices, get_title=None):
    # Print everything to sys.stderr, because stdout is often redirected.
    import sys, functools, builtins
    print = functools.partial(builtins.print, file=sys.stderr)
    input = lambda: print(end='> ') or builtins.input()

    titles = [get_title(x) if get_title else x for x in choices]

    print("Did you mean?")
    for i, title in enumerate(titles, 1):
        print(f"({i}) {title}")

    # Keep track of the number of choices here so we don't need to call `len()` 
    # later on.  This allows the choices argument to be an iterator.
    num_choices = i

    def is_input_ok(x):
        if x.lower() == 'q':
            raise EOFError

        try: x = int(x)
        except ValueError:
            return False

        if x < 1 or x > num_choices:
            return False

        return True

    choice = input()
    
    while not is_input_ok(choice):
        print(f"Please enter a number between 1 and {num_choices}.")
        choice = input()

    return choices[int(choice) - 1]

def slug_from_title(title):

    class Sanitizer: #
        def __getitem__(self, ord): #
            char = chr(ord)
            if char.isalnum(): return char.lower()
            if char in ' _-': return '_'
            # Any other character gets dropped.

    return title.translate(Sanitizer())

def iter_experiments(work, root, recursive=True):
    for path in root.iterdir():
        if not path.is_dir():
            continue

        expt = Experiment(work, path)
        if not expt.check_paths():
            continue

        yield expt
        if recursive:
            yield from iter_experiments(work, expt.root_dir, recursive)

def iter_paths_matching_substr(dir, substr=None, include=None, exclude=None, symlinks=True, include_origin=False):
    substr = '*' if substr is None else f'*{substr}*'
    substr = substr.replace('/', '*/**/*')
    include = _parse_globs(include, substr, ['**/{}', '**/{}/**'])
    exclude = _parse_globs(exclude, substr, '.*')

    matches = sorted(
            Path(x) for x in formic.FileSet(
                directory=dir,
                include=include,
                exclude=exclude,
                symlinks=symlinks,
            )
    )
    if include_origin:
        yield from ((dir, x) for x in matches)
    else:
        yield from matches

def _parse_globs(globs, substr, default):
    if globs is None:
        globs = default
    if isinstance(globs, str):
        globs = [globs]

    return [x.format(substr) for x in globs]




