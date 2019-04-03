#!/usr/bin/env python3

import os
import subprocess

# Make the "documents", "data", and "protocols" directories.  These can't be 
# included directly in the cookiecutter, because they're empty, so can't be 
# part of the actual repository.

os.makedirs('documents', exist_ok=True)
os.makedirs('data', exist_ok=True)
os.makedirs('protocols', exist_ok=True)
os.makedirs('notebook/build', exist_ok=True)

# Make a git repository for the project and make the initial commit.

subprocess.run(['git', 'init'])
subprocess.run(['git', 'add', '.'])
subprocess.run(['git', 'commit', '-m', "Initial commit."])
