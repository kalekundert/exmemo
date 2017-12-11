#!/usr/bin/env python3

import sys
from . import cli
from .. import Workspace, readers, utils
from pprint import pprint

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

    Exmemo looks for protocols both inside and outside of the project.  Inside 
    the project, exmemo just looks in the `protocols/` directory.  Outside the 
    project, exmemo looks in any directory listed in the `shared_protocols` 
    configuration option.  This makes it easy to have protocols that are shared 
    between projects:
    
        shared_protocols = ['~/research/protocols']
    """
    argv = pop_protocol_args('show')
    args = cli.parse_args_via_docopt()
    work = Workspace.from_cwd(strict=False)
    protocol = work.pick_protocol(args['<substr>'])
    reader = readers.pick_reader(protocol, argv)

    reader.show(work)

@cli.priority(20)
def printer():
    """\
    Print the given protocol.

    Usage:
        exmemo [protocol] print <substr>

    Arguments:
        <substr>
            A string specifying the protocol to print.  You can provide any 
            substring from the name of the protocol.  If the substring is not 
            unique, you'll be asked which file you meant.

    Exmemo looks for protocols both inside and outside of the project.  Inside 
    the project, exmemo just looks in the `protocols/` directory.  Outside the 
    project, exmemo looks in any directory listed in the `shared_protocols` 
    configuration option.  This makes it easy to have protocols that are shared 
    between projects:
    
        shared_protocols = ['~/research/protocols']
    """
    argv = pop_protocol_args('print')
    args = cli.parse_args_via_docopt()
    work = Workspace.from_cwd(strict=False)
    protocol = work.pick_protocol(args['<substr>'])
    reader = readers.pick_reader(protocol, argv)

    reader.print(work)

@cli.priority(20)
def save():
    """\
    Save the protocol to a date-stamped text file that can be included in your 
    lab notebook.

    Usage:
        exmemo [protocol] save <substr> [<dir>]

    Arguments:
        <substr>
            A string specifying the protocol to date-stamp and save.  You can 
            provide any substring from the name of the protocol.  If the 
            substring is not unique, you'll be asked which file you meant.

        <dir>
            The directory to save the protocol in.  By default this is just the 
            current working directory.

    Exmemo looks for protocols both inside and outside of the project.  Inside 
    the project, exmemo just looks in the `protocols/` directory.  Outside the 
    project, exmemo looks in any directory listed in the `shared_protocols` 
    configuration option.  This makes it easy to have protocols that are shared 
    between projects:
    
        shared_protocols = ['~/research/protocols']
    """
    argv = pop_protocol_args('save')
    args = cli.parse_args_via_docopt()
    work = Workspace.from_cwd(strict=False)
    protocol = work.pick_protocol(args['<substr>'])
    reader = readers.pick_reader(protocol, argv)

    reader.save(work, args['<dir>'])

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

    Exmemo looks for protocols both inside and outside of the project.  Inside 
    the project, exmemo just looks in the `protocols/` directory.  Outside the 
    project, exmemo looks in any directory listed in the `shared_protocols` 
    configuration option.  This makes it easy to have protocols that are shared 
    between projects:
    
        shared_protocols = ['~/research/protocols']
    """
    args = cli.parse_args_via_docopt()
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

    Exmemo looks for protocols both inside and outside of the project.  Inside 
    the project, exmemo just looks in the `protocols/` directory.  Outside the 
    project, exmemo looks in any directory listed in the `shared_protocols` 
    configuration option.  This makes it easy to have protocols that are shared 
    between projects:
    
        shared_protocols = ['~/research/protocols']
    """
    args = cli.parse_args_via_docopt()
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
    """
    args = cli.parse_args_via_docopt()
    for plugin in readers.get_plugins():
        print(f"{plugin.name}: {' '.join(plugin.extensions)}")


def pop_protocol_args(subcommand):
    cut = sys.argv.index(subcommand) + 2
    sys.argv, protocol_args = sys.argv[:cut], sys.argv[cut:]
    return protocol_args
