#!/usr/bin/env python3

import os
import toml
import subprocess
from subprocess import DEVNULL
from pathlib import Path
from appdirs import AppDirs
from pprint import pprint

app = AppDirs('exmemo')

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
    def protocols_dir(self):
        return self.root_dir / 'protocols'

    def yield_experiments(self, slug=None):
        if slug is None:
            return self.notebook_dir.glob('????????_*/')
        else:
            return self.notebook_dir.glob(f'????????_*{slug}*/')

    @property
    def yield_protocols(self):
        return self.protocols_dir.glob('*')


    def get_notebook_entry(self, dir):
        dir = Path(dir)
        date, slug = dir.name.split('_', 1)
        return dir / f"{slug}.rst"

    def pick_one(self, choices, no_choices=None):
        choices = list(choices)

        if len(choices) == 0:
            raise no_choices or ValueError("No choices to pick from")

        if len(choices) == 1:
            return choices[0]

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
        expts = list(self.yield_experiments(slug))

        if slug is None:
            return expts[-1]  # The most recently created.
        else:
            return self.pick_one(expts)

    def init_project(self, title):
        from cookiecutter.main import cookiecutter
        from click.exceptions import Abort
        from datetime import date

        url = self.config.get('cookiecutter_url') or \
                Path(__file__).parent / 'cookiecutter'

        try:
            cookiecutter(str(url), extra_context={
                    'project_title': title,
                    'year': date.today().year,
            })
        except Abort:
            raise KeyboardInterrupt

    def launch_editor(self, path):

        cmd = os.environ.get('GUI_EDITOR', 'gvim'), path
        subprocess.Popen(cmd, stdout=DEVNULL, stderr=DEVNULL)

    def launch_terminal(self, dir):
        cmd = os.environ.get('TERMINAL', 'sakura'), dir
        subprocess.Popen(cmd, stdout=DEVNULL, stderr=DEVNULL)


class WorkspaceNotFound(IOError):
    show_message_and_die = True

    def __init__(self, dir):
        self.message = f"'{dir}' is not a workspace."



