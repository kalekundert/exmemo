.. image:: brand/logo.png
   :align: center

*Ex memoriam* (or exmemo for short) is a tool for organizing a scientific 
project and keeping a lab notebook, for people who like using the command-line.  
Any files associated with the project are kept in a straight-forward but 
well-thought-out directory tree that you're meant to interact with in the 
shell, and that's also a git repository.  The lab notebook is comprised of 
plain text files (in the restructured text format) that you can write using 
your favorite editor (which should be vim :-D).  These files are rendered to 
HTML by Sphinx (the same tool that is used to document most python projects) 
and can either be viewed locally or uploaded to the internet.  Exmemo also 
provides commands that let you easily refer to files in different parts of the 
projects without having to type full paths, and installs a handful of 
restructured text directives to address some common lad notebook formatting 
needs.  Finally, both exmemo and Sphinx can be heavily extended using python, 
so you can make your notebook work exactly how you want it to.

.. image:: https://img.shields.io/pypi/v/exmemo.svg
   :target: https://pypi.python.org/pypi/exmemo

.. image:: https://img.shields.io/pypi/pyversions/exmemo.svg
   :target: https://pypi.python.org/pypi/exmemo

.. image:: https://img.shields.io/travis/kalekundert/exmemo.svg
   :target: https://travis-ci.org/kalekundert/exmemo

.. image:: https://img.shields.io/coveralls/kalekundert/exmemo.svg
   :target: https://coveralls.io/github/kalekundert/exmemo?branch=master

Installation
============
Install using pip::

   $ pip install exmemo

Usage
=====
At the moment there isn't much online documentation, but the command-line help 
system should have any information you need::

   $ exmemo --help

You can also get help for individual subcommands::

   $ exmemo expt --help

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

   $ exmemo expt new "Large step with half twist"

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
   
   $ exmemo expt edit twist

Note that the experiment is specified by a "slug", in this case "twist".  The 
slug can be any part of the actual experiment name.  If you give a slug that 
matches multiple experiments, you'll be asked which one you meant.  If you 
don't specify a slug at all, the most recent experiment will be opened.

Similarly, you can launch a new terminal that's already cd'd into a particular 
experiment directory using this command::

   $ exmemo expt open twist

When you want to recompile the HTML pages for your notebook, run this command::

   $ exmemo expt build

Now lets say that we're about to go into lab and setup a reaction.  We can 
start by printing out a paper copy of the protocol we want to follow.  (I like 
doing this because I can take notes as I'm working on the paper, then 
transcribe any that are significant back into my notebook when I'm done.)::

   $ exmemo protocol print treadmill

Again the argument to this command ("treadmill") is a slug, but this time 
exmemo will look for matches in your ``protocols/`` directory.  You can also 
tell exmemo to look in directories outside your project (i.e. if you have 
protocols that are shared between projects), see ``exmemo protocols ls --help`` 
for details).

We'd also like to make a copy of this protocol in the experiment subdirectory 
we made, so we can include the protocol in our lab notebook entry.  To do this, 
first launch a terminal that's cd'd into the experiment subdirectory::

   $ exmemo expt open twist

Then run the following command to make a copy of the protocol::

   $ exmemo protocol save treadmill

Text protocols can be included in a restructured text document using the ``..  
literal-include::`` directive, and anything else can be included using the 
``:download:`` role.

Exmemo can also show you a protocol without printing it::

   $ exmemo protocol show treadmill

What exactly this command does depends on what type of file the protocol is.  
Text files will simply be printed to the terminal, python scripts will be 
executed, documents (like *.doc and *.xls) will be opened in libreoffice, and 
PDF files will be opened in your PDF viewer.  You can use the setuptools plugin 
system to provide plugins for new filetypes, or to override the behaviors of 
the existing ones.

Note that there isn't a command to create a new protocol.  Protocols are just 
regular files in the ``protocols/`` directory, so just create them however you 
would normally create a file.

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

   $ exmemo expt open twist

Then run the following command to symlink to some data::

   $ exmemo data link <slug>

Again, you specify which file you're interested in using a slug.  Exmemo will 
search the ``data/`` directory looking for matching files, and will ask you if 
there's any ambiguity.  You can include images in your restructured text files 
using the ``.. figure::`` directive, and any other type of data can be included 
using the ``:download:`` role.

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

Aliases
=======
The exmemo commands are rather verbose, which is not ideal for things you want 
to be typing all the time.  For that reason, I use the following set of shell 
aliases::

   alias en='exmemo expt new'
   alias ee='exmemo expt edit'
   alias eo='exmemo expt open'
   alias es='exmemo protocol show'
   alias ep='exmemo protocol print'
   alias ef='exmemo protocol save'
   alias ey='exmemo data sync'
   alias ek='exmemo data link'
      
Contributing
============
Exmemo is a very new project.  I'm sure there are still lots of bugs and use 
cases I didn't consider.  Both `pull requests 
<https://github.com/kalekundert/exmemo/pulls>` and `bug reports 
<https://github.com/kalekundert/exmemo/issues>' are very welcome.
