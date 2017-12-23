#!/usr/bin/env python3

def ymd():
    from datetime import datetime
    return datetime.today().strftime('%Y%m%d')

def last(iterable):
    yield from (
            (i == len(iterable), x)
            for i, x in enumerate(iterable, 1)
    )

def pick_one(choices):
    # Print everything to sys.stderr, because stdout is often redirected.
    import sys, functools, builtins
    print = functools.partial(builtins.print, file=sys.stderr)
    input = lambda: print(end='> ') or builtins.input()

    print("Did you mean?")
    for i, value in enumerate(choices, 1):
        print(f"({i}) {value}")

    # Keep track of the number of choices here so we don't need to call `len()` 
    # later on.  This allows the choices argument to be an iterator.
    num_choices = i

    def is_input_ok(x):
        if x.lower() == 'q':
            raise EOFError

        try: x = int(x)
        except ValueError:
            return False

        if x < 1 or x > num_choices:
            return False

        return True

    choice = input()
    
    while not is_input_ok(choice):
        print(f"Please enter a number between 1 and {num_choices}.")
        choice = input()

    return int(choice) - 1
