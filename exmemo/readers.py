#!/usr/bin/env python3

import shlex
import shutil
import wet_copy
import subprocess
from pathlib import Path
from fossilize import fossilize
from pprint import pprint

def get_readers():
    from .plugins import get_plugins
    return get_plugins('exmemo.protocolreaders')

def pick_reader(path, args):
    plugins = get_readers()

    for plugin in plugins:
        reader = plugin(path, args)
        if reader.can_handle_path():
            return reader

    raise CantReadProtocol(path, args, plugins)


class Reader:
    extensions = []

    def __init__(self, path, args):
        self.path = Path(path)
        self.args = args
        self.content = None

    def can_handle_path(self):
        return self.path.suffix in self.extensions

    def save(self, work, dir):
        dest = dir / f'{ymd()}_{self.path.name}'
        shutil.copy(self.path, dest)


class TxtReader(Reader):
    priority = 0
    extensions = ['.txt', '.md', '.rst']

    def show(self, work):
        with self.path.open() as file:
            print(file.read().strip())

    def edit(self, work):
        work.launch_editor(self.path)

    def print(self, work):
        wet_copy.print_protocol(self.path)

    def save(self, work, dir):
        fossilize(self.path, f'{dir}/$.txt')


class ScriptReader(Reader):
    priority = 0
    extensions = {
            '.py': 'python',
            '.sh': 'bash',
    }

    def show(self, work):
        cmd = self.extensions[self.path.suffix], *self.command
        subprocess.run(cmd)

    def edit(self, work):
        work.launch_editor(self.path)

    def print(self, work):
        wet_copy.print_protocol(self.command_str)

    def save(self, work, dir):
        fossilize(self.command, f'{dir or "."}/$.txt')

    @property
    def command(self):
        return (self.path, *self.args)

    @property
    def command_str(self):
        return ' '.join(shlex.quote(str(x)) for x in self.command)


class DocReader(Reader):
    priority = 0
    extensions = ['.docx', '.doc', '.xlsx', '.xls', '.odt', '.ods']

    def show(self, work):
        cmd = 'libreoffice', self.path
        subprocess.Popen(cmd)

    def edit(self, work):
        raise CantEditProtocol(self)

    def print(self, work):
        office = 'libreoffice', '--headless', '--invisible', '--convert-to-pdf', self.path
        lpr = 'lpr', '-o', 'sides=one-sided', f'{self.path.stem}.pdf'

        subprocess.run(office)
        subprocess.run(lpr)


class PdfReader(Reader):
    priority = 0
    extensions = ['.pdf']

    def show(self, work):
        work.launch_pdf(self.path)

    def edit(self, work):
        raise CantEditProtocol(self)

    def print(self, work):
        lpr = 'lpr', '-o', 'sides=one-sided', f'{self.path}'
        subprocess.run(lpr)



class CantReadProtocol(Exception):
    show_message_and_die = True

    def __init__(self, path, args, plugins):
        self.message = f"""\
Can't read '{' '.join([str(path), *args])}'.
Tried using the following plugins: {', '.join(x.name for x in plugins)}"""


class CantEditProtocol(Exception):
    show_message_and_die = True

    def __init__(self, reader):
        self.message = f"""\
Can't edit '{reader.path}'.
Editing is not supported by the '{reader.name}' plugin."""
