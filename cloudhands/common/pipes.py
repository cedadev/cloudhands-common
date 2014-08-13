#!/usr/bin/env python3
#   encoding: UTF-8

import ast
import asyncio
import os
from pprint import pprint
import sys

__doc__ = """
Provides an interprocess Queue for use with the asyncio event loop.
"""


class PipeQueue:

    @staticmethod
    def pipequeue(*args, **kwargs):
        return PipeQueue(*args, **kwargs).__enter__()

    @staticmethod
    def get_when_ready(fObj, q):
        payload = fObj.readline().rstrip("\n")
        q.put_nowait(ast.literal_eval(payload))

    def __init__(self, path, history=True):
        self.path = path
        self.history = history
        self._q = asyncio.Queue()

    def __enter__(self):
        try:
            os.mkfifo(self.path)
        except FileExistsError:
            if not self.history:
                raise

        fd = os.open(self.path, os.O_RDONLY | os.O_NONBLOCK)
        self._out = os.fdopen(fd, 'r', buffering=1, encoding="utf-8")
        self._in = open(self.path, "w", buffering=1, encoding="utf-8")

        loop = asyncio.get_event_loop()
        loop.add_reader(fd, PipeQueue.get_when_ready, self._out, self._q)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        if not self.history:
            os.remove(self.path)
        return False

    @asyncio.coroutine
    def get(self):
        rv = yield from self._q.get()
        return rv

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
        loop = asyncio.get_event_loop()
        loop.remove_reader(self._out.fileno())
        self._out.close()
        self._in.close()
