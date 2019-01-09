#!/usr/bin/env python3

from . import cli
from .. import Workspace

@cli.priority(40)
def init():
    """\
    Create a directory layout for a new project.  This layout will include 
    directories for data files, analysis scripts, protocols, notebook entries, 
    and documents.

    Usage:
        exmemo [project] init <title>

    Argument:
        <title>
            The title of the project.  This will be used to make nicely 
            formatted headers in various places, so it should be title-cased 
            and the words should be separated by spaces, e.g.

                "Anglo-French Silly Walk"

            Note that you have to quote the title, otherwise the shell will 
            interpret it as multiple arguments.

    This command will create the following directory structure:

    analysis/
       A python package containing code used for data analysis.  By virtue of 
       being a package, this code can be run from anywhere in the project.  
       You'll need to install it before you can use it:

          $ pip install -e analysis

    data/
       A single directory for any data file you collect.  Data files that are 
       relevant to a particular experiment can be symlinked into the notebook 
       directory using `exmemo data link`.  By  default, this directory is 
       ignored by git.

    documents/
       A directory for presentations, papers, and the like.  By default, this 
       directory is ignored by git.

    notebook/
       A Sphinx directory with separate directories for each experiment you 
       carry out.  An experiment is defined by asking and answering a single 
       question, which may take a single day or several months.

    protocols/
       A directory for protocols, which can be text files, python script, Excel 
       files, Word documents, whatever.
            
    Exmemo is fairly opinionated about which files to create and what to call 
    them, but for the most part these opinions are arbitrary and you can change 
    any you don't like.  The only things you shouldn't change are the names of 
    the directories in the project root.

    There are two ways to override exmemo's opinions.  The quick and easy way 
    is just to manually rename or edit any files.  The more thorough way is to 
    create a custom cookiecutter for your new projects and to tell exmemo about 
    it.  Cookiecutter (https://github.com/audreyr/cookiecutter) is a tool that 
    create new directory layouts from a template.  You can override exmemo's 
    default template by setting the 'cookiecutter_url' in one of the config 
    files, for example `~/.config/exmemo/conf.toml`:

        cookiecutter_url = https://github.com/yourname/cookiecutter-exmemo.git
    """
    args = cli.parse_args_via_docopt()
    work = Workspace('.')

    work.init_project(args['<title>'])

def root():
    """
    Print the root directory of the project.

    Usage:
        exmemo project root
    """
    args = cli.parse_args_via_docopt()
    work = Workspace.from_cwd()

    print(work.root_dir)


