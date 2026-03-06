#!/usr/bin/env python3.12

from exmemo import Workspace

work = Workspace.from_path(__file__)

for expt in work.iter_experiments(recursive=True):
    link_path = expt.root_dir / expt.LINK_PATH
    if link_path.exists():
        link_path.unlink()

    link_path.symlink_to(
            work.root_dir.relative_to(link_path.parent, walk_up=True),
            target_is_directory=True,
    )
