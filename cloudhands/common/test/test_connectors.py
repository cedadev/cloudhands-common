#!/usr/bin/env python3
# encoding: UTF-8

import sqlite3
import unittest

from cloudhands.common.connectors import initialise
from cloudhands.common.connectors import Registry

from cloudhands.common.schema import State


class ConnectionTest(unittest.TestCase):

    def tearDown(self):
        r = Registry()
        r.disconnect(sqlite3, ":memory:")

    def test_initialise_db(self):
        r = Registry()
        con = r.connect(sqlite3, ":memory:")
        self.assertEqual(0, con.session.query(State).count())

        n = initialise(con.session)
        self.assertNotEqual(0, n)
        self.assertGreaterEqual(n, con.session.query(State).count())

        self.assertEqual(0, initialise(con.session))

    def test_connect_and_disconnect(self):
        r = Registry()
        self.assertEqual(0, len(list(r.items)))
        con = r.connect(sqlite3, ":memory:")
        self.assertEqual(1, len(list(r.items)))

        dup = r.connect(sqlite3, ":memory:")
        self.assertIs(con.engine, dup.engine)
        self.assertEqual(1, len(list(r.items)))

        dis = r.disconnect(sqlite3, ":memory:")
        self.assertEqual(0, len(list(r.items)))
        self.assertIs(dup.engine, dis.engine)
        self.assertIs(None, dis.session)

        dup = r.connect(sqlite3, ":memory:")
        self.assertIsNot(con.engine, dup.engine)
        self.assertEqual(1, len(list(r.items)))
