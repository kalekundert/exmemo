.. image:: brand/logo.png
   :align: center

*Ex memoriam* (or exmemo for short) is a tool for organizing a scientific 
project and keeping a lab notebook, for people who like using the command-line.  
Any files associated with the project are kept in a straight-forward but 
well-thought-out directory tree that you're meant to interact with in the 
shell, and that's also a git repository.  The lab notebook is comprised of 
plain text files (in the restructured text format) that you can write using 
your favorite editor (which should be vim 😃).  These files are rendered to 
HTML by Sphinx (the same tool that is used to document most python projects) 
and can either be viewed locally or uploaded to the internet.  Exmemo also 
provides commands that let you easily refer to files in different parts of the 
project without having to type full paths, and installs a handful of 
restructured text directives to address some common lab notebook formatting 
needs.  Finally, both exmemo and Sphinx can be heavily extended using python, 
so you can make your notebook work exactly how you want it to.

.. image:: https://img.shields.io/pypi/v/exmemo.svg
   :target: https://pypi.python.org/pypi/exmemo

.. image:: https://img.shields.io/pypi/pyversions/exmemo.svg
   :target: https://pypi.python.org/pypi/exmemo

.. image:: https://img.shields.io/travis/kalekundert/exmemo.svg
   :target: https://travis-ci.org/kalekundert/exmemo

Installation
============
Install using pip::

   $ pip install exmemo

Usage
=====
At the moment there isn't much online documentation, but the command-line help 
system should have any information you need::

   $ exmemo --help
   Manage a project directory.

   Usage:
       exmemo <command> [<args>...]
       exmemo (-h | --help)
       exmemo --version

   Commands:
       init:     Create a directory layout for a new project.
       new:      Create a new experiment with a blank notebook entry.
       edit:     Open the notebook entry for the given experiment in a text [...]
       open:     Open a new terminal cd'd into the given experiment.
       build:    Render the lab notebook to HTML using Sphinx.
       browse:   Open the rendered lab notebook in a web browser.
       show:     Display the given protocol.
       print:    Print the given protocol.
       archive:  Save the protocol to a date-stamped text file that can be [...]
       sync:     Import data into the project from any available source.
       link:     Make a symbolic link to the indicated data file.
       project:  Manage the entire project.
       note:     Keep notes on your day-to-day experiments.
       protocol: Manage, display, and print protocols.
       data:     Interact with data files.
       config:   Get and set configuration options.
       debug:    Print information that can help diagnose problems with exmemo.

You can also get help for individual subcommands::

   $ exmemo note --help

Example
=======
If you're just getting started with exmemo, the first step is to create a new 
project directory::

   $ exmemo init "Silly Walks"

This command takes the name of the project in title-case.  It'll prompt you for 
some more information, then create and fill in a project directory for you.  
The project will have the following directories:

``analysis/``
   A python package containing code used for data analysis.  By virtue of being 
   a package, this code can be run from anywhere in the project.

``data/``
   A single directory for any data file you collect.  Data files that are 
   relevant to a particular experiment can be symlinked into the notebook 
   directory.

``documents/``
   A directory for presentations, papers, and the like.

``notebook/``
   A Sphinx directory with separate directories for each experiment you carry 
   out.  Each experiment is meant to ask and answer a single question, whether
   that takes a single day or several months.

``protocols/``
   A directory for protocols, which can be text files, python script, Excel 
   files, Word documents, whatever.

Let's start by creating a new entry (called an "experiment") in our lab 
notebook::

   $ exmemo note new "Large step with half twist"

This will create a subdirectory called ``20171210_large_step_with_half_twist/`` 
in the ``notebook/`` directory.  It will also create a restructured text file 
in that directory and automatically open it in your editor.  (You can control 
which editor is used either by setting the $EDITOR environment variable or by 
editing one of exmemo's config files; see ``exmemo config --help``.)  One of 
the ideas behind exmemo is that files related to a particular experiment --- 
notebook entries, raw data, analysis scripts, figures, etc. --- should be 
stored together.  That's what this subdirectory is for.

When you later want to edit the notebook entry again, you can do so from 
anywhere in the project directory with the following command::
   
   $ exmemo note edit twist

Note that you can specify the experiment by giving just part of its name.  If 
you give a substring that matches multiple experiments, you'll be asked which 
one you meant.  If you don't specify an experiment at all, the most recent one 
will be opened.

Similarly, you can launch a new terminal that's already cd'd into a particular 
experiment directory using this command::

   $ exmemo note open twist

When you want to recompile the HTML pages for your notebook, run this command::

   $ exmemo note build

Now lets say that we're about to go into lab and actually do an experiment.  We 
can start by printing out a paper copy of the protocol we want to follow.  (I 
like doing this because I can take notes as I'm working on the paper, then 
transcribe any that are significant back into my notebook when I'm done.)::

   $ exmemo protocol print treadmill

Again the argument to this command ("treadmill") can just be a substring, but 
this time exmemo will look for matches in your ``protocols/`` directory.  You 
can also tell exmemo to look in directories outside your project (i.e. if you 
have protocols that are shared between projects), see ``exmemo protocols ls 
--help`` for details).

We'd also like to make a copy of this protocol in the experiment subdirectory 
we made, so we can include the protocol in our lab notebook entry.  To do this, 
first launch a terminal that's cd'd into the experiment subdirectory::

   $ exmemo note open twist

Then run the following command to make a date-stamped copy of the protocol::

   $ exmemo protocol archive treadmill

Text protocols can be included in a restructured text document using the ``..  
literal-include::`` directive, and anything else can be included using the 
``:download:`` role.

Exmemo can also show you a protocol without printing it::

   $ exmemo protocol show treadmill

What exactly this command does depends on what type of file the protocol is.  
Text files will simply be printed to the terminal, python scripts will be 
executed, documents (like \*.doc and \*.xls) will be opened in libreoffice, and 
PDF files will be opened in your PDF viewer.  You can use the setuptools plugin 
system to provide plugins for new filetypes, or to override the behaviors of 
the existing ones.

Note that there isn't a command to create a new protocol.  Protocols are just 
regular files in the ``protocols/`` directory, so just create them however you 
would normally `create files <https://xkcd.com/378/>`_.

Protocol in hand, we do our experiment and get some data.  Let's say this data 
is on our USB drive.  Exmemo has a command to automatically sync data from 
different sources into the project, but first we need to configure it.  So we 
put the following lines in the ``.exmemorc`` file in the root directory of the 
project::

   [[data]]
   type = 'usb'
   src = '~/usb/treadmill'
   mountpoint = '~/usb'

This specifies that exmemo should look for data in the ``~/usb/treadmill`` 
directory of your USB drive, which is mounted as ``~/usb``.  Any data the 
exmemo finds will be rsync'd into the ``data/`` directory of the project.  
Exmemo will also try to automatically mount and unmount the USB drive, if it 
doesn't seem to be mounted when you run the command.

Now we can sync our data, so we plug in the USB drive and run the following 
command::

   $ exmemo data sync

If we want to include this data in our notebook or do some analysis on it, we 
should symlink it into the subdirectory we made for this experiment.  (Again, 
this keeps all the files relevant to a particular question in one place.)  To 
do this, the first step is to fire up a terminal that's cd'd into the 
experiment subdirectory::

   $ exmemo note open twist

Then run the following command to symlink to some data::

   $ exmemo data link <substr>

Again, you can specify which file you're interested in using just a substring.  
Exmemo will search the ``data/`` directory looking for matching files, and will 
ask you if there's any ambiguity.  You can include images in your restructured 
text files using the ``.. figure::`` directive, and any other type of data can 
be included using the ``:download:`` role.

Why initially copy the data into the ``data/`` directory, just to symlink it 
into an experiment subdirectory later?  There are a couple reasons.  First, 
data files are often large and binary, so keeping them in one places makes it 
easier to handle them specially when doing backups or making commits.  Second, 
not every data file ends up in an experiment.  Some data just doesn't need to 
be analyzed and displayed in your notebook.  Other data are just not associated 
with any experiment (i.e. gels from routine cloning).

Exmemo has some other features as well, but this covers the main workflow.  
Again, the command-line help messages are pretty good, so start there if you're 
looking for more details.

Collaborating
=============
If you want other people to be able to read your notebook without necessarily 
being able to edit it, the best option is to publish the HTML files generated 
by Sphinx on the internet somewhere.  If you don't mind your files being public 
(or are willing to pay to keep them private), ReadTheDocs is a nice service for 
this.  Otherwise it's not to hard to setup a webserver that uses Apache 
authentication to keep your files private.

If you want other people to be able to read and edit your notebook, the best 
option is to use git.  The project directory is already a git repository, so 
you just need to push it to GitHub and add anyone you want to work with as a 
collaborator.  As before, you can either pay GitHub or setup your own git 
server if you want to keep your files private (although GitHub is often willing 
to give free private repositories to academic researchers).

Aliases
=======
The exmemo commands are rather verbose, which is not ideal for things you want 
to be typing all the time.  There are shortcuts for some of the most common 
commands (e.g. ``exmemo edit`` instead of ``exmemo note edit``) and you can 
make any command a little shorter by only typing the first few letters of each 
subcommand (i.e.  ``exmemo ed`` instead of ``exmemo edit``), but it's still not 
ideal.  For that reason, I use the following set of shell aliases::

   alias en='exmemo note new'
   alias ee='exmemo note edit'
   alias eo='exmemo note open'
   alias eb='exmemo note build'
   alias el='exmemo note ls'
   alias ew='exmemo note browse'
   alias eww='exmemo note browse -w'
   alias eps='exmemo protocol show'
   alias epp='exmemo protocol print'
   alias epe='exmemo protocol edit'
   alias epl='exmemo protocol ls'
   alias epr='exmemo protocol archive'
   alias edy='exmemo data sync'
   alias edk='exmemo data link'
   alias edg='exmemo data gel'

   function ed () {
       d=$(exmemo note directory "$@")
       [ $? = 0 ] && cd $d || echo $d  # Don't try to cd if something goes wrong.
   }

Contributing
============
Exmemo is a very new project.  I'm sure there are still lots of bugs and use 
cases I didn't consider.  Both `pull requests 
<https://github.com/kalekundert/exmemo/pulls>`_ and `bug reports 
<https://github.com/kalekundert/exmemo/issues>`_ are very welcome.
