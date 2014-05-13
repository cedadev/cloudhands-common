#!/usr/bin/env python3
# encoding: UTF-8

from collections import OrderedDict
from collections.abc import MutableMapping
from collections.abc import MutableSequence

import pkg_resources

__doc__ = """
This module discovers entry points in installed packages

"""


def discover(id):
    for ep in pkg_resources.iter_entry_points(id):
        try:
            obj = ep.load(require=False)
        except Exception as e:
            continue
        else:
            yield (ep.name, obj)

fsms = [i[1] for i in discover("jasmin.component.fsm")]
"""This is the collection of all discovered state machines.
Each entry point declared as a ``jasmin.component.fsm`` should be a class
you have generated with :py:func:`cloudhands.common.schema.fsm_factory`.
"""

providers = dict(discover("jasmin.burst.provider"))
"""This is the collection of all discovered provider configurations.
Each entry point declared as a ``jasmin.site.settings`` should be a python
ConfigParser_ object. Its name is used as the `provider` string.

.. _ConfigParser: http://docs.python.org/3.3/library/configparser.html
"""

settings = dict(discover("jasmin.site.settings"))
"""This is the collection of all discovered key-value mappings.
Each entry point declared as a ``jasmin.site.settings`` should be a python
ConfigParser_ object. Its name is used as the `provider` string.

.. _ConfigParser: http://docs.python.org/3.3/library/configparser.html
"""

bundles = [i[1] for i in discover("jasmin.ssl.bundle")]
"""This is the collection of all discovered certificate bundles.
Each entry point declared as a ``jasmin.ssl.bundle`` should be a file
path.
"""

catalogue = OrderedDict(discover("jasmin.portal.catalogue"))
"""This is the collection of all cloud catalogue items. Each entry point
declared under ``jasmin.portal.catalogue` should be a View object.
"""

if __name__ == "__main__":
    print(*["{:^10} {}".format(k, v) for k, v in globals().items()
          if isinstance(v, MutableMapping)
          or isinstance(v, MutableSequence)], sep="\n")
