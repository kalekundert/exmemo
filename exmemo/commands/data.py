#!/usr/bin/env python3

import subprocess
from . import cli
from .. import Workspace
from pathlib import Path
from pprint import pprint

def sync():
    """\
    Import data into the project from any available source.

    Usage:
        exmemo [data] sync [-v]

    Options:
        -v --verbose
            Print out each command that is run to sync the data.

    You can define data sources in any of your config files.  Each data source 
    must have a type and any arguments defined by that type.  For example:

        [[data]]
        type: usb
        src: ~/usb/gels
        dest: gels

    This specifies that data from `~/usb/gels` should be copied into the `gels` 
    directory within the data directory of the project using `rsync`.
    """
    args = cli.parse_args_via_docopt()
    work = Workspace.from_cwd()

    # Add usage text for each collector to the docstring.
    #from ..collectors import get_collectors

    work.sync_data(args['--verbose'])

def link():
    """
    Make a symbolic link to the indicated data file.

    Usage:
        exmemo [data] link <slug> [<dir>]

    Arguments
        <slug>
            A string specifying the data file to link.  You can provide any 
            substring from the name of the data file.  If the substring is not 
            unique, you'll be asked which file you meant.

        <dir>
            The directory where the link will be created.  By default, this is 
            the current working directory ('.').
            
    This command is most commonly used to link data files into particular 
    experiments in the notebook directory.  Thus the data directory is a 
    repository for all of your data, and the notebook directory is a curated 
    set of only the most important or relevant data.
    """
    args = cli.parse_args_via_docopt()
    work = Workspace.from_cwd()
    data = work.pick_data(args['<slug>'])
    link = Path(args['<dir>'] or '.') / data.name

    link.symlink_to(data)

def gel():
    """
    Format a gel for inclusion in the lab notebook.  In particular, this means 
    converting it from a *.tif to a *.png, inverting it's colors, and giving 
    you a chance to crop it.

    Usage:
        exmemo data gel <slug> [<dir>] [-f]

    Arguments:
        <slug>
            A string specifying the data file to copy and crop.  You can 
            provide any substring from the name of the data file.  If the 
            substring is not unique, you'll be asked which file you meant.

        <dir>
            The directory where the image will be copied.  By default, this is 
            the current working directory ('.').

    Options:
        -f, --force
            Overwrite any existing image.

    This command is commonly used to copy gels into the notebook directory.  
    The full resolution images stay in the data directory, but you can make a 
    nicely formatted copy to show in the notebook.
    """
    args = cli.parse_args_via_docopt()
    work = Workspace.from_cwd()
    data = work.pick_data(args['<slug>'])
    copy = Path(args['<dir>'] or '.') / f'{data.stem}.png'

    if copy.exists() and not args['--force']:
        raise FileAlreadyExists(copy)

    convert = 'convert', str(data), '-fill', 'white', '-opaque', 'red', '-negate', str(copy)
    gimp = 'gimp', str(copy)

    subprocess.run(convert)
    subprocess.Popen(gimp)

def ls():
    """\
    List data files.

    Usage:
        exmemo data ls [<slug>]

    Arguments:
        <slug>
            Only list files that contain the given substring.
    """
    args = cli.parse_args_via_docopt()
    work = Workspace.from_cwd()

    for path in work.iter_data(args['<slug>']):
        print(path.relative_to(work.data_dir))


class FileAlreadyExists(Exception):
    show_message_and_die = True

    def __init__(self, path):
        self.message = f"Refusing to overwrite {path}"



