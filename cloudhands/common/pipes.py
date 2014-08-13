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
