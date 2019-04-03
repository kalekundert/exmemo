#!/usr/bin/env python3

import os
import shlex
import subprocess
from pathlib import Path

def get_collectors():
    from .plugins import get_plugins
    return {x.name: x for x in get_plugins('exmemo.datacollectors')}

def sync_data(work, verbose):
    collectors = get_collectors()

    for config in work.config.get('data', []):
        try: type = config.pop('type')
        except KeyError:
            raise UnspecifiedCollectorType(config)

        try: collector_cls = collectors[type]
        except KeyError:
            raise UnknownCollectorType(type, collectors)

        collector = collector_cls(**config)
        collector.sync(work, verbose)

def run(cmd, verbose=True, **kwargs):
    if cmd is None:
        return
    if verbose:
        cmd_str = cmd if isinstance(cmd, str) else ' '.join(str(x) for x in cmd)
        print(f'$ {cmd_str}')
    return subprocess.run(cmd, **kwargs)


class RsyncCollector:
    """
    Copy any files that have changed from the given (and possibly remote) 
    source to the given destination within the project data directory.  The 
    following options are recognized:

    src (required):
        The file or directory to copy, relative to the project data 
        directory.  If you want to specify a directory, remember that 
        trailing slashes are significant to rsync: 'dir' means copy dir 
        itself, 'dir/' means copy only the files inside dir.
       
    dest (default: '.'):
        Where to copy the files to, relative to the project data directory.
       
    cmd (default: 'rsync --archive --ignore-existing {src} {dest}'):
        The rsync command to execute.  {src} and {dest} will be replaced 
        with the values of the `src` and `dest` options, respectively.  The 
        command will be run from the project data directory.  The purpose 
        of this option is to allow you to pass rsync different flags, or 
        even to run a different command entirely.

    precmd (default: ''):
        A shell command to execute before running rsync.  The command will 
        be run from the project data directory.

    postcmd (default: ''):
        A shell command to execute after running rsync.  The command will 
        be run from the project data directory.
    """

    def __init__(self, src, dest=None, cmd=None, precmd=None, postcmd=None):
        # Use `os.path.expanduser()` for `src` because it doesn't clobber 
        # trailing slashes, which are significant to rsync.
        self.src = os.path.expanduser(src)
        self.dest = Path(dest or '.').expanduser()
        self.cmd = cmd or 'rsync --archive --ignore-existing {src} {dest}'
        self.precmd = precmd or ''
        self.postcmd = postcmd or ''

    def sync(self, work, verbose):
        dest = work.data_dir / self.dest
        paths = dict(src=self.src, dest=dest)
        rsync = [x.format(**paths) for x in shlex.split(self.cmd)]

        for precmd in self.precmd.split('\n'):
            run(precmd, verbose, cwd=work.data_dir, shell=True)

        # Shell-mode disabled to eliminate the possibility of getting 
        # confused by spaces/quotes/whatever in file names.
        run(rsync, verbose, cwd=work.data_dir, shell=False)

        for postcmd in self.postcmd.split('\n'):
            run(postcmd, verbose, cwd=work.data_dir, shell=True)
    

class UsbCollector(RsyncCollector):
    """
    Copy files from a USB drive into the project.  Rsync is used to 
    actually copy the files, so large directories can be efficiently copied 
    and all of the options that apply to the 'rsync' collector also apply 
    here.
    
    src (required):
        The file or directory to copy.  If you want to specify a directory, 
        remember that trailing slashes are significant to rsync: 'dir' 
        means copy dir itself, 'dir/' means copy only the files inside dir.
       
    dest (default: '.'):
        Where to copy the files to, relative to the project data directory.

    mountpoint (default: None):
        The directory where the USB drive is mounted.  If this is 
        specified, exmemo will attempt to automatically mount and unmount 
        the USB drive if it can't otherwise locate the files.  If this 
        option is not specified, the USB drive must be mounted before the 
        sync command is run.
       
    cmd (default: 'rsync --archive --ignore-existing {src} {dest}'):
        The rsync command to execute.  {src} and {dest} will be replaced 
        with the values of the `src` and `dest` options, respectively.  The 
        command will be run from the project data directory.  The purpose 
        of this option is to allow you to pass rsync different flags, or 
        even to run a different command entirely.

    precmd (default: ''):
        A shell command to execute before running rsync, but after the USB 
        drive has been mounted.  The command will be run from the project 
        data directory.
    

    postcmd (default: ''):
        A shell command to execute after running rsync, but before the USB 
        drive has been unmounted.  The command will be run from the project 
        data directory.
    .
    """

    def __init__(self, src, dest=None, mountpoint=None, rsync=None, precmd=None, postcmd=None):
        super().__init__(src, dest, rsync, precmd, postcmd)
        self.mountpoint = mountpoint and Path(mountpoint).expanduser()

    def sync(self, work, verbose):
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
                err = run(cmd, verbose).returncode
                umount_when_done = (err == 0)

        if os.path.exists(self.src):
            super().sync(work, verbose)
        elif verbose:
            print(f"Can't find {self.src}.")

        if umount_when_done:
            cmd = 'umount', self.mountpoint
            err = run(cmd, verbose).returncode
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



# Make the collector docstrings line up right when they're indented and 
# included in a usage string.
# vim: tw=75
