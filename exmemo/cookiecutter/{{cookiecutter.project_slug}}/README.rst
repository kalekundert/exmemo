analysis/

   A python package containing code used for data analysis.  By virtue of being 
   a package, this code can be run from anywhere in the project.  If this is 
   your first time working with the project, you'll need to install the 
   analysis package before you can use it

      $ pip install -e analysis

   The `-e` flag installs the package in such a way that any changes you make 
   to the sourcefile are automatically reflected in the installation (i.e. you 
   don't need to reinstall the package for changes to take effect).

data/

   A single directory for any data file you collect.  Data files that are 
   relevant to a particular experiment can be symlinked into the notebook 
   directory.  By default, this directory is ignored by git.  Some relevant 
   commands:

   - `exmemo data sync`: Import any new data available.

documents/

   A directory for presentations, papers, and the like.  By default, this 
   directory is ignored by git.

notebook/

   A Sphinx directory with separate directories for each experiment you carry 
   out.  Each experiment is meant to ask and answer a single question, whether 
   that takes a single day or several months.  Some relevant commands:
   
   - `exmemo expt new`: Start a new experiment
   - `exmemo expt edit`: Edit an existing experiment

protocols/
   
   A directory for protocols, which can be text files, python script, Excel 
   files, Word documents, whatever.  Some relevant commands:

   - `exmemo protocol print`: Print out a particular protocol
