#!/usr/bin/env python3
# encoding: UTF-8

import unittest

from cloudhands.common.types import NamedDict
from cloudhands.common.types import NamedList


class TestNamedDict(unittest.TestCase):

    def test_001(self):
        d = NamedDict(a=1, b=2).name("testname")
        self.assertEqual(1, d["a"])
        self.assertEqual(2, len(d))
        self.assertEqual("testname", d.name)


class TestNamedList(unittest.TestCase):

    def test_001(self):
        d = NamedList([1, 2]).name("testname")
        self.assertEqual(1, d[0])
        self.assertEqual(2, d[1])
        self.assertEqual(2, len(d))
        self.assertEqual("testname", d.name)
