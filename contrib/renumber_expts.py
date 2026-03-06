from exmemo import Workspace
from itertools import count
import re

work = Workspace.from_path(__file__)

old_ids = work._load_expt_map()

new_ids = dict(zip(
    sorted(old_ids),
    count(1),
))

debug(old_ids, new_ids)

for old_id, expt in old_ids.items():
    old_notes = expt.note_path.read_text()
    new_notes = re.sub(
            pattern=r':expt:`(\d+)`', 
            repl=lambda m: f':expt:`{new_ids[int(m.group(1))]}`',
            string=old_notes,
    )
    expt.note_path.write_text(new_notes)

    expt.assign_id(new_ids[old_id], overwrite=True)

