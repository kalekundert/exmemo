#!/usr/bin/env python3

import os
import shlex
import subprocess
from pathlib import Path
from pprint import pprint

def get_collectors():
    from .plugins import get_plugins
    return {x.name: x for x in get_plugins('exmemo.datacollectors')}

def sync_data(work):
    collectors = get_collectors()

    for config in work.config.get('data', []):
        try: type = config.pop('type')
        except KeyError:
            raise UnspecifiedCollectorType(config)

        try: collector_cls = collectors[type]
        except KeyError:
            raise UnknownCollectorType(type, collectors)

        collector = collector_cls(**config)
        collector.sync(work)


class VerboseMixin:

    def run(self, cmd, **kwargs):
        if cmd is None:
            return
        if self.verbose:
            cmd_str = cmd if isinstance(cmd, str) else ' '.join(str(x) for x in cmd)
            print(f'$ {cmd_str}')
        return subprocess.run(cmd, **kwargs)


class RsyncCollector(VerboseMixin):

    def __init__(self, src, dest, cmd=None, precmd=None, postcmd=None, verbose=False):
        # Use `os.path.expanduser()` for `src` because it doesn't clobber 
        # trailing slashes, which are significant to rsync.
        self.src = os.path.expanduser(src)
        self.dest = Path(dest).expanduser()
        self.cmd = cmd or 'rsync --archive --ignore-existing {src} {dest}'
        self.precmd = precmd
        self.postcmd = postcmd
        self.verbose = verbose

    def sync(self, work):
        dest = work.data_dir / self.dest
        rsync = shlex.split(self.cmd.format(src=self.src, dest=dest))

        for precmd in self.precmd.split('\n'):
            self.run(precmd, cwd=work.data_dir, shell=True)

        self.run(rsync)

        for postcmd in self.postcmd.split('\n'):
            self.run(postcmd, cwd=work.data_dir, shell=True)
    

class UsbCollector(RsyncCollector):

    def __init__(self, src, dest, mountpoint=None, rsync=None, precmd=None, postcmd=None, verbose=False):
        super().__init__(src, dest, rsync, precmd, postcmd, verbose)
        self.mountpoint = mountpoint and Path(mountpoint).expanduser()

    def sync(self, work):
        """
        Copy files from the given location on a USB drive into the project.
        """

        def is_mounted():
            cmd = 'mountpoint', '-q', self.mountpoint
            return subprocess.run(cmd).returncode == 0

        umount_when_done = False

        if not os.path.exists(self.src):

            # Give up if the source doesn't exist and we weren't told how to in
            # mount it.
            if not self.mountpoint:
                return

            if not is_mounted():
                cmd = 'mount', self.mountpoint
                err = self.run(cmd).returncode
                umount_when_done = (err == 0)

        if os.path.exists(self.src):
            super().sync(work)
        elif self.verbose:
            print(f"Can't find {self.src}.")

        if umount_when_done:
            cmd = 'umount', self.mountpoint
            err = self.run(cmd).returncode
            if not err:
                print("USB safe to remove.")



class BadCollectorConfig(Exception):
    show_message_and_die = True

    def __init__(self, config):
        key_value = '\n'.join(f'  {k}: {v}' for k,v in config.items())
        self.message = f"""\
The following data collector is missing a type:

{key_value}"""


class UnknownCollectorType(Exception):
    show_message_and_die = True

    def __init__(self, type, collectors):
        if not collectors:
            self.message = "No data collectors installed."
        else:
            did_you_mean = '\n'.join(f'  {x}' for x in collectors)
            self.message = f"""\
Unknown data collector '{type}'.  Did you mean:

{did_you_mean}"""


