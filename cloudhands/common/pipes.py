#!/usr/bin/env python3
#   encoding: UTF-8

import argparse
from collections import namedtuple
import logging
import os
import sys

Connection = namedtuple("Connection", ["module", "path", "engine", "session"])

__doc__ = """
Spike for message passing over asyncio-wrapped named pipes.
"""

def wait_until_open_for_write(path):
    return open(path, 'w')
    
def main(args):
    path, = args.path
    try:
        os.mkfifo(path)
    except FileExistsError:
        pass

    try:
        pipe = wait_until_open_for_write(path)
    finally:
        os.remove(path)

    return 1

def parser():
    rv = argparse.ArgumentParser(description=__doc__)
    rv.add_argument(
        "--version", action="store_true", default=False,
        help="Print the current version number")
    rv.add_argument(
        "-v", "--verbose", required=False,
        action="store_const", dest="log_level",
        const=logging.DEBUG, default=logging.INFO,
        help="Increase the verbosity of output")
    rv.add_argument(
        "--log", default=None, dest="log_path",
        help="Set a file path for log output")
    rv.add_argument(
        "path", default=None, nargs=1,
        help="Set the path to the named pipe")
    return rv


def run():
    p = parser()
    args = p.parse_args()
    rv = main(args)
    return rv


if __name__ == "__main__":
    sys.exit(run())
