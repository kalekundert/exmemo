#!/usr/bin/env python3

import shutil
import wet_copy
import subprocess
from pathlib import Path
from fossilize import fossilize
from pkg_resources import iter_entry_points, DistributionNotFound

def get_plugins():
    readers = []

    for plugin in iter_entry_points(group='exmemo.protocolreaders'):
        reader = plugin.load()
        reader.name = plugin.name
        readers.append(reader)

    readers.sort(key=lambda x: x.name)
    readers.sort(key=lambda x: x.priority, reverse=True)

    return readers

def pick_reader(path, args):
    plugins = get_plugins()

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
        subprocess.run(self.command)

    def print(self, work):
        wet_copy.print_protocol(self.command_str)

    def save(self, work, dir):
        fossilize(self.path, f'{dir}/$.txt')

    @property
    def command(self):
        return (self.extensions[self.path.suffix], self.path, *self.args)

    @property
    def command_str(self):
        cmd = ' '.join(shlex.quote(x) for x in self.command)


class DocReader(Reader):
    priority = 0
    extensions = ['.docx', '.doc', '.xlsx', '.xls', '.odt', '.ods']

    def show(self, work):
        cmd = 'libreoffice', self.path
        subprocess.Popen(cmd)

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

    def print(self, work):
        lpr = 'lpr', '-o', 'sides=one-sided', f'{self.path}'
        subprocess.run(lpr)



class CantReadProtocol(Exception):
    show_message_and_die = True

    def __init__(self, path, args, plugins):
        self.message = f"""\
Can't read '{' '.join([str(path), *args])}'.
Tried using the following plugins: {', '.join(x.name for x in plugins)}"""
