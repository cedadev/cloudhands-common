#!/usr/bin/env python3
#   encoding: UTF-8

import argparse
import ast
import asyncio
from collections import namedtuple
from contextlib import ExitStack
import logging
import os
from pprint import pprint
import sys

Connection = namedtuple("Connection", ["module", "path", "engine", "session"])

__doc__ = """
Spike for message passing over asyncio-wrapped named pipes.
"""

# prototyping
import unittest

class PipeQueueTest(unittest.TestCase):

    def setUp(self):
        self.path = "test.fifo"
        try:
            os.remove(self.path)
        except FileNotFoundError:
            pass

    def tearDown(self):
        self.setUp()

    def test_no_history(self):
        os.mkfifo(self.path)
        self.assertRaises(
            FileExistsError,
            PipeQueue(self.path, history=False).__enter__)

    def test_attributes(self):
        with PipeQueue(self.path) as pq:
            self.assertIsNotNone(pq._in)
            self.assertIsNotNone(pq._out)
            self.assertTrue(hasattr(pq, "get"))
            self.assertTrue(hasattr(pq, "put"))

    def test_simple_read_write(self):
        loop = asyncio.get_event_loop()
        with PipeQueue(self.path) as pq:
            loop.run_until_complete(pq.put("S"))
            rv = loop.run_until_complete(pq.get())
            self.assertEqual("S", rv)

    def test_tuple_read_write(self):
        loop = asyncio.get_event_loop()
        payload = (12, "string")
        with PipeQueue(self.path) as pq:
            loop.run_until_complete(pq.put(payload))
            rv = loop.run_until_complete(pq.get())
            self.assertEqual(payload, rv)

    def test_multiple_read_write(self):
        loop = asyncio.get_event_loop()
        payloads = ((i, "string") for i in range(6))
        with PipeQueue(self.path) as pq:
            for n, payload in enumerate(payloads):
                loop.run_until_complete(pq.put(payload))

            for i in range(n):
                rv = loop.run_until_complete(pq.get())
                self.assertIsInstance(rv, tuple)
                self.assertEqual(i, rv[0])
                self.assertEqual("string", rv[1])

    def test_queue_returned_by_factory(self):

        def factory():
            return PipeQueue.pipequeue(self.path)

        loop = asyncio.get_event_loop()
        pq = factory()
        loop.run_until_complete(pq.put("S"))
        rv = loop.run_until_complete(pq.get())
        self.assertEqual("S", rv)
        pq.close()

class PipeQueue:

    @staticmethod
    def pipequeue(*args, **kwargs):
        return PipeQueue(*args, **kwargs).__enter__()

    def __init__(self, path, history=True):
        self.path = path
        self.history = history

    def __enter__(self):
        try:
            os.mkfifo(self.path)
        except FileExistsError:
            if not self.history:
                raise

        self._out = os.fdopen(
            os.open(self.path, os.O_RDONLY | os.O_NONBLOCK),
            buffering=1,
            encoding="utf-8")
        self._in = open(self.path, "w", buffering=1, encoding="utf-8")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        if not self.history:
            os.remove(self.path)
        return False

    @asyncio.coroutine
    def get(self):
        future = asyncio.Future()
        payload = self._out.readline().rstrip("\n")
        future.set_result(ast.literal_eval(payload))
        return future 

    @asyncio.coroutine
    def put(self, msg):
        future = asyncio.Future()
        try:
            pprint(msg, stream=self._in, compact=True, width=sys.maxsize)
        except TypeError:  # 'compact' is new in Python 3.4
            pprint(msg, stream=self._in, width=sys.maxsize)
        future.set_result(msg)
        return future

    def close(self): 
        self._out.close()
        self._in.close()

def main(args):
    path, = args.path
    try:
        os.mkfifo(path)
    except FileExistsError:
        pass

    loop = asyncio.get_event_loop()
    future = asyncio.Future()
    asyncio.Task(wait_until_open_for_write(future, path))
    future.add_done_callback(pipe_open_for_write)

    try:
        fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
        loop.run_forever()
    finally:
        loop.close()
        os.close(fd)
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
    unittest.main()
    sys.exit(run())
