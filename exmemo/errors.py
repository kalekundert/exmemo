#!/usr/bin/env python3

class ExMemoError(Exception):
    pass

class IntegrityError(ExMemoError):
    show_message_and_die = True

class UserError(ExMemoError):
    show_message_and_die = True

class WorkspaceNotFound(UserError):

    def __init__(self, dir):
        self.message = f"'{dir}' is not a workspace."

class ExperimentNotFound(UserError):

    def __init__(self, id):
        super().__init__(f"no such experiment '{id}'")

class CantMatchSubstr(UserError):

    def __init__(self, type, substr):
        self.message = f"No {type} matching '{substr}'."

