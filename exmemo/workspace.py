#!/usr/bin/env python3

import os
import sys
import platform
import toml
import formic
import shlex
import subprocess
import collections
import autoprop
import signature_dispatch
import nestedtext as nt
import voluptuous

from subprocess import DEVNULL
from datetime import datetime
from collections.abc import Mapping, MutableSet
from contextlib import contextmanager
from pathlib import Path
from appdirs import AppDirs
from more_itertools import one, all_unique
from reprfunc import repr_from_init
from . import utils
from .errors import *

app = AppDirs('exmemo')

_BASE_STATUSES = {'new', 'ready', 'in progress', 'complete', 'abandoned'}
_BLOCKABLE_STATUSES = {'new', 'ready', 'in progress'}
_TERMINAL_STATUSES = {'complete', 'abandoned'}

# I want a more flexible API for looking up experiments:
# - Search whole notebook?  Just the current directory?  Recursively? 
# - Search by ID, substring, or path?
# - Expect one hit or many?  What to do if too many/few hits found?

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
        self._expts = None

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
    def notebook_build_dir(self):
        return self.root_dir / '.cache' / 'exmemo' / 'notebook' 

    @property
    def has_project_files(self):
        if not self.rcfile.exists():
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
        dir = Path().cwd() / slug
        rst = dir / 'notes.rst'

        if not os.path.isdir(dir):
            dir.mkdir()
        else:
            sys.exit('Experiment exists. Use exmemo [note] edit [<substr>].')

        with rst.open('w') as file:
            file.write(f"""\
{'*' * len(title)}
{title}
{'*' * len(title)}
""")

        self.assign_experiment_ids()
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
        expts = self._load_expt_map()
        try:
            return expts[id]
        except KeyError:
            raise ExperimentNotFound(id) from None

    def find_experiments(self, ids):
        expts = self._load_expt_map()
        return [expts[x] for x in ids]

    def find_all_experiments(self):
        return self._load_expt_map()

    def pick_experiment(self, id_or_tag=None):
        try:
            id = int(id_or_tag)

        except (ValueError, TypeError):
            if id_or_tag is None:
                return Experiment.from_dir(os.getcwd(), self)

            else:
                return pick_via_tag(
                    id_or_tag,
                    self.find_all_experiments().values(),
                    get_path=lambda x: x.root_dir_rel,
                    get_extra_score=lambda x: x.id,
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


    def _load_expt_map(self):
        if self._expts is not None:
            return self._expts

        self._expts = expts = {}

        for expt in self.iter_experiments():
            id = expt.id
            if id is None:
                continue
            if id in expts:
                raise IntegrityError(f"multiple experiments with id #{id}---this should never happen and must be repaired manually")

            expts[id] = expt

        return expts

    __repr__ = repr_from_init(
            positional=['root'],
            attrs={'root': '_root'},
    )

@autoprop
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

    ID_PATH = '.expt/id'
    LINK_PATH = '.expt/root'
    NOTES_PATHS = 'notes.rst', 'notes.md'
    STATUS_PATH = '.expt/status'
    PREREQS_PATH = '.expt/prereqs'
    TAGS_PATH = '.expt/tags'

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
        return cls.from_sphinx_doc(env, env.docname, work=work, strict=strict)

    @classmethod
    def from_sphinx_doc(cls, env, doc, work=None, strict=True):
        doc_path = Path(env.doc2path(doc))
        return cls.from_dir(doc_path.parent, work=work, strict=strict)


    def __init__(self, work, root):
        self._work = work
        self._root = Path(root).resolve()

        self._id = None
        self._status = None
        self._blocked = None
        self._prereqs = Prereqs(work, self._root / self.PREREQS_PATH)
        self._tags = Tags(self._root / self.TAGS_PATH)

    def __eq__(self, other):
        return self._root == other._root

    def __hash__(self):
        return hash(self._root)

    def __repr__(self):
        rel_dir = self.root_dir.relative_to(self.workspace.notebook_dir)
        return f"{self.__class__.__qualname__}(root='{rel_dir}')"

    def get_workspace(self):
        return self._work

    def get_root_dir(self):
        return self._root

    def get_root_dir_rel(self):
        return self._root.relative_to(self._work.notebook_dir)

    def get_note_path(self):
        for name in self.NOTES_PATHS:
            path = self._root / name
            if path.exists():
                return path

        return self._root / self.NOTES_PATHS[0]

    def get_id(self):
        if self._id is None:
            id_path = self._root / self.ID_PATH
            try:
                self._id = int(id_path.read_text())
            except (NotADirectoryError, FileNotFoundError):
                pass

        return self._id

    def get_parent(self):
        return self.get_ancestor(1)

    def get_ancestor(self, level):
        parent = self.from_dir(self.root_dir.parent, work=self.workspace)

        if level == 1:
            return parent
        elif level > 1:
            return parent.get_ancestor(level - 1)
        else:
            raise UserError(f"level must be ≥ 1, not {level}")

    def get_title(self):
        notes = self.note_path.read_text()
        return notes.splitlines()[1]

    def get_status(self):
        if self._status is None:
            status_path = self._root / self.STATUS_PATH

            if status_path.exists():
                self._status = status_path.read_text().strip()
            else:
                self._status = 'new'

            if self._status not in _BASE_STATUSES:
                raise IntegrityError(f"expt #{self.id} has unknown status: {status}")

        if any(self.blocking_prereqs) and self._status in _BLOCKABLE_STATUSES:
            return 'blocked'
        else:
            return self._status

    def set_status(self, status):
        if status not in _BASE_STATUSES:
            raise IntegrityError(f"expt #{self.id} has unknown status: {status}")

        self._status = status

        status_path = self._root / '.expt' / 'status'
        status_path.parent.mkdir(exist_ok=True)
        status_path.write_text(status)

    def get_done(self):
        return self.status in _TERMINAL_STATUSES

    def get_prereqs(self):
        return self._prereqs

    def get_prereq_ids(self):
        return {x.id for x in self._prereqs}

    def get_blocking_prereqs(self):
        return {x for x in self._prereqs if not x.done}

    def get_blocking_prereq_ids(self):
        return {x.id for x in self.blocking_prereqs}

    def get_tags(self):
        return self._tags

    def get_priority(self):
        if self._priority is None:
            try:
                priority_path = self._root / '.expt' / 'priority'
                self._priority = int(priority_path.read_text())
            except (NotADirectoryError, FileNotFoundError):
                pass

        return self._priority

    def check_paths(self):
        return self.note_path.exists() and any(
                self.workspace.notebook_dir.samefile(x)
                for x in self.root_dir.parents
        )

    def assign_id(self, id, *, overwrite=False):
        """
        Set the id for this experiment.

        The caller takes responsibility for ensuring that the given id is not 
        already in use by another experiment.  This is especially true when 
        using the *overwrite* argument.
        """

        if id is None:
            raise IntegrityError(f"can't assign {id!r} as an experiment id number")

        # I didn't implement this as the setter for the id property, because 
        # ids are not meant to be changed once initially set.
        if self.id is not None and not overwrite:
            raise IntegrityError(f"can't assign id #{id} to experiment #{self.id}")

        id_path = self._root / self.ID_PATH
        id_path.parent.mkdir(exist_ok=True)
        id_path.write_text(f'{id}\n')

        self._id = id

        # This doesn't belong here; I should refactor...
        if not overwrite:
            link_path = self._root / self.LINK_PATH
            link_path.symlink_to(
                    self.workspace.root_dir,
                    target_is_directory=True,
            )

    def require_id(self):
        """
        Return this experiment's id, and assign one if necessary.
        """
        if self._id is None:
            self._work.assign_experiment_ids()

        assert self._id is not None
        return self._id

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

    __repr__ = repr_from_init(
            positional=['root'],
            skip=['work'],
            attrs={'root': '_root'},
    )

# These exceptions are a mess:
# - Don't inherit from a common class
# - Too fine-grained
# - Don't set message in superclass

class Tags(Mapping):
    """
    A tag is a key/value pair that describes some aspect of an experiment (e.g. 
    method=pcr).  Experiments can have any number of tags, and can have 
    multiple values for the same tag (e.g. method=pcr and method=ivtt). This 
    class manages all of the tags associated with a particular experiment.

    This class behaves much like a dictionary of sets, where the keys are the 
    tag names and the sets are the tag values.  The tag values must be strings.  
    Any changes made to the tags are immediately saved to the filesystem.
    """

    def __init__(self, path):
        if path.exists() and not path.is_dir():
            raise ValueError(f"expected directory, got: {path}")

        self._tags_dir = path
        self._tags = None

    def __repr__(self):
        return repr(self._tags or {})

    def __getitem__(self, key):
        tags = self._load_tags()
        return tags.__getitem__(key)

    def __setitem__(self, key, values):
        values = self_require_set_of_strings(key)
        self._record_tag(key, list(values))

    def __delitem__(self, key):
        self._record_tag(key, [])

    def __iter__(self):
        tags = self._load_tags()
        return tags.__iter__()

    def __len__(self):
        tags = self._load_tags()
        return tags.__len__()

    def add(self, key, value):
        with self._update_tag(key) as values:
            values.append(value)

    def discard(self, key, value):
        with self._update_tag(key) as values:
            try:
                values.remove(value)
            except ValueError:
                pass

    def _load_tags(self):
        """
        Load the dict-of-sets data structure from the file system.
        """
        if self._tags is None:
            try:
                self._tags = {
                        p.name: set(self._load_tag(p.name))
                        for p in self._tags_dir.iterdir()
                }
            except FileNotFoundError:
                self._tags = {}

        return self._tags

    def _load_tag(self, key):
        # Note that this function returns a list instead of a set.  The reason 
        # for this is to allow us to add/remove items from this data structure 
        # without reordering lines in the underlying file, which would lead to 
        # bigger and more confusing version control diffs.  For example, it's 
        # possible the user may need to resolve merge conflicts in tag files.
        tag_path = self._tags_dir / key

        try:
            values = nt.load(tag_path, top=list)
        except FileNotFoundError:
            values = []

        values = self._require_list_of_strs(values)
        return values

    def _record_tag(self, key, values):
        # Note that this function expects a list rather than a set.  See 
        # `_load_tag()` for the rationale.
        values = self._require_list_of_strs(values)
        tag_path = self._tags_dir / key

        if values:
            self._tags_dir.mkdir(parents=True, exist_ok=True)
            nt.dump(values, tag_path)
            if self._tags:
                self._tags[key] = set(values)

        else:
            tag_path.unlink(missing_ok=True)
            if self._tags:
                self._tags.pop(key, None)

    @contextmanager
    def _update_tag(self, key):
        values = self._load_tag(key)
        yield values
        self._record_tag(key, values)

    def _require_set_of_strs(self, values):
        schema = voluptuous.Schema({str})
        try:
            return schema(values)
        except: 
            raise IntegrityError("tags must be sets of strings, not: {values!r}")

    def _require_list_of_strs(self, values):
        schema = voluptuous.Schema([str])
        try:
            values = schema(values)
        except volutuous.Invalid: 
            raise IntegrityError("tags must be list of strings, not: {values!r}")

        if not all_unique(values):
            raise IntegrityError("found duplicate tag values: {value!r}")

        return values

class Prereqs(MutableSet):
    """
    A prerequisite is an experiment that must be completed before the current 
    one.  This information is used to work out which experiments are ready to 
    start working on.  

    This class behaves as a set that immediately saves any changes made to it 
    to the filesystem.
    """

    def __init__(self, work, path):
        if path.exists() and not path.is_dir():
            raise ValueError(f"expected directory, got: {path}")

        self._work = work
        self._prereqs_dir = path
        self._prereqs = None

    def __repr__(self):
        return repr(self._prereqs)

    @signature_dispatch
    def __contains__(self, id: int):
        return any(id == x.id for x in self)

    @signature_dispatch
    def __contains__(self, expt: Experiment):
        prereqs = self._load_prereqs()
        return prereqs.__contains__(expt)

    def __iter__(self):
        prereqs = self._load_prereqs()
        return prereqs.__iter__()

    def __len__(self):
        prereqs = self._load_prereqs()
        return prereqs.__len__()

    @signature_dispatch
    def add(self, id: int):
        expt = self._work.find_experiment(id)
        self.add(expt)

    @signature_dispatch
    def add(self, expt: Experiment):
        self._prereqs_dir.mkdir(parents=True, exist_ok=True)
        prereq_path = self._prereqs_dir / str(expt.require_id())
        prereq_path.touch(exist_ok=True)

        if self._prereqs is not None:
            self._prereqs.add(expt)

    @signature_dispatch
    def discard(self, id: int):
        expt = self._work.find_experiment(id)
        self.discard(expt)

    @signature_dispatch
    def discard(self, expt: Experiment):
        prereq_path = self._prereqs_dir / str(expt.require_id())
        prereq_path.unlink(missing_ok=True)

        if self._prereqs is not None:
            self._prereqs.discard(prereq)


    def _load_prereqs(self):
        if self._prereqs is None:
            if not self._prereqs_dir.exists():
                self._prereqs = {}
            else:
                prereq_ids = {int(p.name) for p in self._prereqs_dir.iterdir()}
                self._prereqs = self._work.find_experiments(prereq_ids)

        return self._prereqs

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
        if default:
            return default
        else:
            raise no_default or no_matches

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
        return utils.pick_one_via_cli(matches, get_path)

def slug_from_title(title):

    class Sanitizer: #
        def __getitem__(self, ord): #
            char = chr(ord)
            if char.isalnum(): return char.lower()
            if char in ' _-': return '_'
            # Any other character gets dropped.

    return title.translate(Sanitizer())

def iter_experiments(work, root, recursive=True):
    if not root.exists():
        return

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




