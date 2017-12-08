#!/usr/bin/env python3

import os
import toml
import formic
import shlex
import subprocess
import collections
from subprocess import DEVNULL
from datetime import datetime
from pathlib import Path
from appdirs import AppDirs
from pprint import pprint
from . import readers

app = AppDirs('exmemo')

def ymd():
    return datetime.today().strftime('%Y%m%d')

def slug_from_title(title):

    class Sanitizer: #
        def __getitem__(self, ord): #
            char = chr(ord)
            if char.isalnum(): return char.lower()
            if char in ' _-': return '_'
            # Any other character gets dropped.

    return title.translate(Sanitizer())

def yield_paths_matching_slug(dir_or_dirs, slug=None, glob='{}', exclude=['.*'], symlinks=True):
    if isinstance(dir_or_dirs, (str, Path)):
        dirs = [dir_or_dirs]
    else:
        dirs = dir_or_dirs

    glob = glob.format('*' if slug is None else f'*{slug}*')

    for dir in dirs:
        matches = formic.FileSet(
                directory=dir,
                include=glob,
                exclude=exclude,
                symlinks=symlinks,
        )
        yield from (Path(x) for x in matches)


class Workspace:

    @classmethod
    def from_dir(cls, dir):
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

        dir = given_dir = Path(dir).resolve()
        workspace = None

        while not looks_like_workspace(dir):
            dir = dir.parent
            if dir == Path('/'):
                raise WorkspaceNotFound(given_dir)

        return workspace

    @classmethod
    def from_cwd(cls):
        """
        Create a workspace object containing given directory (or the current 
        working directory, by default).  This involves descending the directory 
        hierarchy looking for the root of the project, which should contain a 
        characteristic set of files and directories.
        """
        return cls.from_dir('.')


    def __init__(self, root):
        self._root = Path(root).resolve()

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
    def protocols_dirs(self):
        return [self.protocols_dir] + self.shared_protocols_dirs

    @property
    def protocols_dir(self):
        return self.root_dir / 'protocols'

    @property
    def shared_protocols_dirs(self):
        return [Path(x).expanduser() for x in self.config.get('shared_protocols', [])]

    def yield_experiments(self, slug=None):
        yield from (x.parent for x in yield_paths_matching_slug(
            self.notebook_dir, slug, f'/{8*"[0-9]"}_{{0}}/{{0}}.rst'))

    def yield_protocols(self, slug=None):
        yield from self.yield_local_protocols(slug)
        yield from self.yield_shared_protocols(slug)

    def yield_local_protocols(self, slug=None):
        return yield_paths_matching_slug(self.protocols_dir, slug)

    def yield_shared_protocols(self, slug=None):
        return yield_paths_matching_slug(self.shared_protocols_dirs, slug)

    def yield_data(self, slug=None):
        return yield_paths_matching_slug(self.data_dir, slug)

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
        print("Did you mean?")
        for i, value in enumerate(choices, 1):
            print(f"({i}) {value.name}")

        def is_input_ok(x):
            try: x = int(x)
            except ValueError:
                return False

            if x < 1 or x > len(choices):
                return False

            return True

        prompt = '> '
        choice = input(prompt)
        
        while not is_input_ok(choice):
            print(f"Please enter a number between 1 and {len(choices)}.")
            choice = input(prompt)

        return choices[int(choice) - 1]

    def pick_experiment(self, slug):
        return self.pick_path(slug, self.yield_experiments(slug))

    def pick_protocol(self, slug):
        return self.pick_path(slug, self.yield_protocols(slug))

    def pick_protocol_reader(self, path, args):
        path = Path(path)
        return readers.pick_reader(path, args)

    def pick_data(self, slug):
        return self.pick_path(slug, self.yield_data(slug))

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
        expt = self.notebook_dir / f'{ymd()}_{slug}'
        rst = expt / f'{slug}.rst'

        expt.mkdir()
        with rst.open('w') as file:
            file.write(f"""\
{'*' * len(title)}
{title}
{'*' * len(title)}
""")

        self.launch_editor(rst)

    @property
    def editor(self):
        return self.config.get('editor', os.environ.get('EDITOR')) or 'vim'

    @property
    def terminal(self):
        return self.config.get('terminal', os.environ.get('TERMINAL')) or 'xterm'

    @property
    def pdf_viewer(self):
        return self.config.get('pdf', os.environ.get('PDF')) or 'evince'

    def launch_editor(self, path):
        cmd = *shlex.split(self.editor), path
        subprocess.Popen(cmd)

    def launch_terminal(self, dir):
        cmd = self.term,
        subprocess.Popen(cmd, cwd=dir, stdout=DEVNULL, stderr=DEVNULL)

    def launch_pdf(self, path):
        cmd = self.pdf_viewer, path
        subprocess.Popen(cmd)

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



