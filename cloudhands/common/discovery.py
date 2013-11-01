#!/usr/bin/env python3
# encoding: UTF-8

from collections.abc import MutableSequence

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

fsms = list(discover("jasmin.component.fsm"))
"""
This is the collection of all discovered state machines.
Each entry point declared as a ``jasmin.component.fsm`` should be a class
you have generated with :py:func:`cloudhands.common.schema.fsm_factory`.
"""

settings = list(discover("jasmin.site.settings"))
"""
This is the collection of all discovered key-value mappings.
Each entry point declared as a ``jasmin.site.settings`` should be a python
ConfigParser_ object.

.. _ConfigParser: http://docs.python.org/3.3/library/configparser.html
"""

bundles = list(discover("jasmin.ssl.bundle"))
"""
This is the collection of all discovered certificate bundles.
Each entry point declared as a ``jasmin.ssl.bundle`` should be a file
path.
"""


if __name__ == "__main__":
    print(*["{:^10} {}".format(k, v) for k, v in globals().items()
          if isinstance(v, MutableSequence)], sep="\n")
