#!/usr/bin/env python3

import pytest
import parametrize_from_file

from parametrize_from_file import Namespace, defaults, cast, error_or
from voluptuous import Schema, Coerce

with_py = Namespace()
with_exmemo = Namespace(
        'import exmemo',
        'from exmemo import *',
)

Int = Coerce(int)
Float = Coerce(float)


