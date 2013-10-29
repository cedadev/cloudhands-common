#!/usr/bin/env python3
# encoding: UTF-8

import pkg_resources

__doc__ = """
Here is a list of the registered APIs:

jasmin.component.fsm
--------------------

Pluggable FSM interface.
"""


def discover(id):
    for i in pkg_resources.iter_entry_points(id):
        try:
            ep = i.load(require=False)
        except Exception as e:
            continue
        else:
            yield ep

fsm = list(discover("jasmin.component.fsm"))
