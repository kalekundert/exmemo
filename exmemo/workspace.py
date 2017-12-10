#!/usr/bin/env python3

import os
import toml
import formic
import shlex
import subprocess
import collections
from subprocess import DEVNULL
from pathlib import Path
from appdirs import AppDirs
from pprint import pprint
from . import readers, utils

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

        def looks_like_workspace(dir):
            nonlocal workspace
            workspace = Workspace(dir)

            if not workspace.rcfile.exists():
                return False
            if not workspace.analysis_dir.exists():
                return False
            if not workspace.data_dir.exists():
                return False
            if not workspace.documents_dir.exists():
                return False
            if not workspace.notebook_dir.exists():
                return False
            if not workspace.protocols_dir.exists():
                return False

            return True

        dir = given_dir = Path(dir)
        workspace = None

        while not looks_like_workspace(dir):
            dir = dir.parent
            if dir == Path('/'):
                if strict: raise WorkspaceNotFound(given_dir)
                else: return Workspace(given_dir)

        return workspace

    @classmethod
    def from_cwd(cls, strict=True):
        """
        Create a workspace object containing given directory (or the current 
        working directory, by default).  This involves descending the directory 
        hierarchy looking for the root of the project, which should contain a 
        characteristic set of files and directories.
        """
        # Use `os.getenv('PWD')` to avoid resolving symlinks, if possible.  
        # This helps keep any paths that get outputted looking nice.
        return cls.from_dir(os.getenv('PWD', os.getcwd()), strict)


    def __init__(self, root):
        # Use `os.path.abspath()` instead of `Path.resolve()` to avoid 
        # resolving any symlinks in the path.
        self._root = Path(os.path.abspath(root))

        config_paths = [
                Path(app.site_config_dir) / 'conf.toml',
                Path(app.user_config_dir) / 'conf.toml',
                self.rcfile,
        ]
        config_paths = [
                str(x) for x in config_paths if x.exists()
        ]
        if not config_paths:
            self._config = {}
        else:
            self._config = toml.load(config_paths)

    @property
    def root_dir(self):
        return self._root

    @property
    def config(self):
        return self._config

    @property
    def rcfile(self):
        return self.root_dir / '.exmemorc'

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
    def protocols_dir(self):
        return self.root_dir / 'protocols'

    @property
    def protocols_dirs(self):
        local_dirs = [self.protocols_dir]
        shared_dirs = [Path(x).expanduser() for x in self.config.get('shared_protocols', [])]
        return [x for x in local_dirs + shared_dirs if x.exists()]

    def iter_data(self, slug=None):
        return iter_paths_matching_slug(self.data_dir, slug)
    
    def iter_experiments(self, slug=None):
        yield from (x.parent for x in iter_paths_matching_slug(
            self.notebook_dir, slug, f'/{8*"[0-9]"}_{{0}}/{{0}}.rst'))

    def iter_protocols(self, slug=None):
        for dir in self.protocols_dirs:
            yield from iter_paths_matching_slug(dir, slug)

    def iter_protocols_from_dir(self, dir, slug=None):
        yield from iter_paths_matching_slug(dir, slug)

    def pick_path(self, slug, choices, no_choices=None):
        choices = list(choices)

        if len(choices) == 0:
            raise no_choices or ValueError("No choices to pick from")

        if len(choices) == 1:
            return choices[0]

        if slug is None:
            return choices[-1]  # The most recently created.

        # Once I've written the config-file system, there should be an option 
        # to change how this works (i.e. CLI vs GUI vs automatic choice).
        i = utils.pick_one(x.name for x in choices)
        return choices[i]

    def pick_data(self, slug):
        return self.pick_path(slug, self.iter_data(slug))

    def pick_experiment(self, slug):
        return self.pick_path(slug, self.iter_experiments(slug))

    def pick_protocol(self, slug):
        return self.pick_path(slug, self.iter_protocols(slug))

    def pick_protocol_reader(self, path, args):
        path = Path(path)
        return readers.pick_reader(path, args)

    def init_project(self, title):
        from cookiecutter.main import cookiecutter
        from click.exceptions import Abort

        url = self.config.get('cookiecutter_url') or \
                Path(__file__).parent / 'cookiecutter'

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

        expt.mkdir()
        with rst.open('w') as file:
            file.write(f"""\
{'*' * len(title)}
{title}
{'*' * len(title)}
""")

        self.launch_editor(rst)

    def launch_editor(self, path):
        editor = self.config.get('editor', os.environ.get('EDITOR')) or 'vim'
        cmd = *shlex.split(editor), path
        subprocess.Popen(cmd)

    def launch_terminal(self, dir):
        term = self.config.get('terminal', os.environ.get('TERMINAL')) or 'xterm'
        cmd = shlex.split(term)
        subprocess.Popen(cmd, cwd=dir, stdout=DEVNULL, stderr=DEVNULL)

    def launch_pdf(self, path):
        pdf = self.config.get('pdf', os.environ.get('PDF')) or 'evince'
        cmd = *shlex.split(pdf), path
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

    def get_notebook_entry(self, dir):
        dir = Path(dir)
        date, slug = dir.name.split('_', 1)
        return dir / f"{slug}.rst"

    def get_data_collectors():
        pass


class WorkspaceNotFound(IOError):
    show_message_and_die = True

    def __init__(self, dir):
        self.message = f"'{dir}' is not a workspace."



def slug_from_title(title):

    class Sanitizer: #
        def __getitem__(self, ord): #
            char = chr(ord)
            if char.isalnum(): return char.lower()
            if char in ' _-': return '_'
            # Any other character gets dropped.

    return title.translate(Sanitizer())

def iter_paths_matching_slug(dir, slug=None, glob=None, exclude=['.*'], symlinks=True, include_origin=False):
    slug = '*' if slug is None else f'*{slug}*'

    if glob is None:
        include = [f'**/{slug}', f'**/{slug}/**']  # Match files and dirs.
    else:
        include = glob.format(slug)

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


