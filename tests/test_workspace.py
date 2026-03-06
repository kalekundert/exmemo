#!/usr/bin/env python3

import parametrize_from_file

from exmemo.workspace import *
from param_helpers import *

def dict_of_sets(d):
    return {k: set(v) for k, v in d.items()}

def set_of_expts(work, given):
    return set(work.find_experiments(map(int, given)))


@parametrize_from_file(indirect=['tmp_files'])
def test_tags_load(tmp_files, expected):
    tags = Tags(tmp_files)
    assert tags == dict_of_sets(expected)

@parametrize_from_file(
        schema=defaults(tmp_files={}, expected_files={}, deleted_files=[]),
        indirect=['tmp_files'],
)
def test_tags_update(tmp_files, update, expected, expected_files, deleted_files):
    tags = Tags(tmp_files)
    with_py.fork(tags=tags).exec(update)

    assert tags == dict_of_sets(expected)

    for file, contents in expected_files.items():
        path = tmp_files / file
        assert path.read_text().strip() == contents

    for file in deleted_files:
        path = tmp_files / file
        assert not path.exists()

@parametrize_from_file(indirect=['tmp_files'])
def test_prereqs_load(tmp_files, prereqs_dir, expected):
    work = Workspace(tmp_files)
    prereqs = Prereqs(work, tmp_files / prereqs_dir)
    assert prereqs == set_of_expts(work, expected)

@parametrize_from_file(
        schema=defaults(tmp_files={}, expected_files={}, deleted_files=[]),
        indirect=['tmp_files'],
)
def test_prereqs_update(tmp_files, prereqs_dir, update, expected, expected_files, deleted_files):
    work = Workspace(tmp_files)
    prereqs = Prereqs(work, tmp_files / prereqs_dir)
    with_py.fork(prereqs=prereqs).exec(update)

    assert prereqs == set_of_expts(work, expected)

    for file in expected_files:
        path = tmp_files / file
        assert path.exists()

    for file in deleted_files:
        path = tmp_files / file
        assert not path.exists()

# Test cases:
# - No status set: new
# - Status set: each status
#   - Check done as well
#
# - Blocked by prereqs:
#   - Blockable statues: blocked
#   - Other statuses: unchanged

# I can test all that just by loading from the file system.
#
# Also add an exec parameter, so I can test explicitly changing things.

@parametrize_from_file(
        schema=[
            defaults(exec='pass'),
            cast(expected=Schema({Int: str})),
            with_exmemo.error_or('expected'),
        ],
        indirect=['tmp_files'],
)
def test_experiment_status(tmp_files, exec, expected, error):
    work = Workspace(tmp_files)
    with_expts = with_py.fork(
            work=work,
            EXPT=work.find_all_experiments(),
    )

    with error:
        with_expts.exec(exec)

        for id, status in expected.items():
            expt = work.find_experiment(id)
            assert expt.status == status

            # Check that the status is persistent:
            work_persist = Workspace(tmp_files)
            expt_persist = work_persist.find_experiment(id)
            assert expt_persist.status == status

