#!/usr/bin/env python3

import toml
from . import cli
from .. import Workspace
from ast import literal_eval

def get():
    """\
    Get the value of a configuration option.

    Usage:
        exmemo config get <option>
    """
    args = cli.parse_args_via_docopt()
    work = Workspace.from_cwd(strict=False)
    option = args['<option>']

    if option in work.config:
        print(f"{option}: {work.config[option]}")
    else:
        print(f"Option '{option}' is not defined.")

def set():
    """\
    Set a configuration option.

    Usage:
        exmemo config set <option> <value> [--user | --site]

    Options:
        -s --site
            Set the given option in the site-wide configuration file.

        -u --user
            Set the given option in the user-wide configuration file.  This
            is the default behavior if the command is not run from within an 
            exmemo project directory.

    An effort will be made to interpret the given value as a python data type 
    (using `ast.literal_eval`, to be specific), but if this fails the value 
    will be interpreted as a string.  You can put quotes around a value 
    (usually two sets of quotes, since the first will be interpreted by the 
    shell) to force it to be interpreted as a string (for example, if you want 
    to store the literal string "42").
    """
    args = cli.parse_args_via_docopt()
    option, value = args['<option>'], args['<value>']
    work, path = get_config_path(args)

    # Try to interpret the given value as a python data type.
    try: value = literal_eval(value)
    except ValueError: pass

    # Update the config.
    config = toml.load(str(path))
    config[option] = value
    with open(path, 'w') as file:
        toml.dump(config, file)

def edit():
    """\
    Open the configuration file in your editor.

    Usage:
        exmemo config edit [--user | --site]

    Options:
        -s --site
            Open the site-wide configuration file, rather than the one for 
            this project.

        -u --user
            Open the site-wide configuration file, rather than the one for 
            this project.  This is the default behavior if the command is not 
            run from within an exmemo project directory.
    """
    args = cli.parse_args_via_docopt()
    work, path = get_config_path(args)
    work.launch_editor(path)


def get_config_path(args):
    """
    Return the path to the config file indicated by the arguments, along with a 
    workspace.

    This is used by the functions that can edit the config files.  Briefly, if 
    either the '--site' or '--user' option are specified, return the path to 
    the corresponding configuration file.  Otherwise, return the path to the 
    in-project configuration file if the current working directory is in a 
    project, or the user-wide configuration file if it isn't.
    """
    strict = not any((args['--site'], args['--user']))
    work = Workspace.from_cwd(strict=strict)

    if args['--site']:
        path = work.site_config_path
    elif args['--user'] or not work.has_project_files:
        path = work.user_config_path
    else:
        path = work.project_config_path

    return work, path
