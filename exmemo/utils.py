#!/usr/bin/env python3

from .errors import *

def ymd():
    from datetime import datetime
    return datetime.today().strftime('%Y%m%d')

def last(iterable):
    yield from (
            (i == len(iterable), x)
            for i, x in enumerate(iterable, 1)
    )

