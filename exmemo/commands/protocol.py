#!/usr/bin/env python3

import sys
from . import cli
from .. import Workspace, readers, utils

known_extensions = '\n    '.join(
        ' '.join(Reader.extensions)
        for Reader in readers.get_readers()
)
shared_doc = f"""\
Exmemo looks for protocols both inside and outside of the project.  Inside the 
project, exmemo looks in the current working directory and the `protocols/` 
directory (and all of its subdirectories) at the root of the project.  Outside 
the project, exmemo looks in any directory listed in the `shared_protocols` 
configuration option.  See `exmemo config -h` for information on setting 
configuration options.  This makes it easy to have protocols that are shared 
between projects:

    shared_protocols = ['~/research/protocols']

Only protocols with a recognized file extension will be displayed.  
Currently, the following extensions are recognized:
    
    {known_extensions}

Post a bug report if you have protocols of a different type that you would 
like to use with Exmemo.
"""

@cli.priority(20)
def show():
    """\
    Display the given protocol.

    Usage:
        exmemo [protocol] show <substr> [<args>...]

    Arguments:
        <substr>
            A string specifying the protocol to show.  You can provide any 
            substring from the name of the protocol.  If the substring is not 
            unique, you'll be asked which file you meant.

        <args>
            Any information that needs to be passed to the protocol.  This is 
            mostly useful for protocols that are scripts.

    {shared_doc}
    """
    argv = pop_protocol_args('show')
    args = cli.parse_args_via_docopt(shared_doc=shared_doc)
    work = Workspace.from_cwd(strict=False)
    protocol = work.pick_protocol(args['<substr>'])
    reader = readers.pick_reader(protocol, argv)

    reader.show(work)

@cli.priority(20)
def print():
    """\
    Print the given protocol.

    Usage:
        exmemo [protocol] print <substr>

    Arguments:
        <substr>
            A string specifying the protocol to print.  You can provide any 
            substring from the name of the protocol.  If the substring is not 
            unique, you'll be asked which file you meant.

    {shared_doc}
    """
    argv = pop_protocol_args('print')
    args = cli.parse_args_via_docopt(shared_doc=shared_doc)
    work = Workspace.from_cwd(strict=False)
    protocol = work.pick_protocol(args['<substr>'])
    reader = readers.pick_reader(protocol, argv)

    reader.print(work)
    reader.archive(work)

@cli.priority(20)
def archive():
    """\
    Save the protocol to a date-stamped text file that can be included in your 
    lab notebook.

    Usage:
        exmemo [protocol] archive <substr> [<dir>]

    Arguments:
        <substr>
            A string specifying the protocol to archive.  You can provide any 
            substring from the name of the protocol.  If the substring is not 
            unique, you'll be asked which file you meant.

        <dir>
            The directory to save the archive in.  By default this is just the 
            current working directory.

    {shared_doc}
    """
    argv = pop_protocol_args('archive')
    args = cli.parse_args_via_docopt(shared_doc=shared_doc)
    work = Workspace.from_cwd(strict=False)
    protocol = work.pick_protocol(args['<substr>'])
    reader = readers.pick_reader(protocol, argv)

    reader.archive(work, args['<dir>'])

def edit():
    """
    Edit the given protocol.

    Usage:
        exmemo protocol edit <substr>

    Arguments:
        <substr>
            A string specifying the protocol to show.  You can provide any 
            substring from the name of the protocol.  If the substring is not 
            unique, you'll be asked which file you meant.

    {shared_doc}
    """
    args = cli.parse_args_via_docopt(shared_doc=shared_doc)
    work = Workspace.from_cwd(strict=False)
    protocol = work.pick_protocol(args['<substr>'])
    reader = readers.pick_reader(protocol, [])

    reader.edit(work)

def ls():
    """\
    List protocols.

    Usage:
        exmemo protocol ls [<substr>]

    Arguments:
        <substr>
            Only list files that contain the given substring.

    {shared_doc}
    """
    args = cli.parse_args_via_docopt(shared_doc=shared_doc)
    work = Workspace.from_cwd(strict=False)

    for last, dir in utils.last(work.protocols_dirs):
        print(dir)
        for path in work.iter_protocols_from_dir(dir, args['<substr>']):
            print(' ', path.relative_to(dir))
        if not last:
            print()

def plugins():
    """
    List every installed plugin for reading protocols.

    Usage:
        exmemo protocol plugins

    You can create plugins to add support for file extensions that aren't 
    understood by Exmemo natively.  A plugin is a class, usually pretty simple, 
    with methods describing how to show, edit, print, and save a protocol of a 
    particular file type.  Look in ``exmemo/reader.py`` for examples of how to 
    write such a class, and ``setup.py`` for examples of how to install them.
    """
    args = cli.parse_args_via_docopt()
    for plugin in readers.get_readers():
        print(f"{plugin.name}: {' '.join(plugin.extensions)}")


def pop_protocol_args(subcommand):
    cut = sys.argv.index(subcommand) + 2
    sys.argv, protocol_args = sys.argv[:cut], sys.argv[cut:]
    return protocol_args
