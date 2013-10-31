#!/usr/bin/env python3
# encoding: UTF-8

import pkg_resources

__doc__ = """
This module discovers entry points in installed packages

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
"""
This is the programmatic aggregate of all discovered state machines.
Each entry point declared as a ``jasmin.component.fsm`` should be a class
you have generated with :py:func:`cloudhands.common.schema.fsm_factory`.
"""
