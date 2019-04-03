#!/usr/bin/env python3

import shlex
import subprocess
from pathlib import Path

def test_init(tmpdir, monkeypatch):
    monkeypatch.chdir(tmpdir)

    subprocess.run(
            shlex.split('exmemo init "Silly Walks"'),
            input='\n'.join(['John Cleese', 'jcleese', '', '', '2018', ]),
            encoding='utf8',
    )
    subpaths = [
            ('silly_walks',),
            ('silly_walks', 'analysis'),
            ('silly_walks', 'analysis', 'silly_walks'),
            ('silly_walks', 'analysis', 'tests'),
            ('silly_walks', 'analysis', 'setup.py'),
            ('silly_walks', 'data',),
            ('silly_walks', 'documents'),
            ('silly_walks', 'notebook'),
            ('silly_walks', 'notebook', 'conf.py'),
            ('silly_walks', 'notebook', 'index.rst'),
            ('silly_walks', 'notebook', 'ideas_and_feedback.rst'),
            ('silly_walks', 'notebook', 'unexpected_observations.rst'),
            ('silly_walks', 'protocols'),
    ]
    for subpath in subpaths:
        assert tmpdir.join(*subpath).check()

