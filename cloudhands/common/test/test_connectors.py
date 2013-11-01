#!/usr/bin/env python3
# encoding: UTF-8

import sqlite3
import unittest

from cloudhands.common.connectors import Initialiser
from cloudhands.common.connectors import Session
from cloudhands.common.connectors import SQLite3Client

from cloudhands.common.discovery import fsms

from cloudhands.common.schema import State


class SQLite3ClientTest(SQLite3Client, unittest.TestCase):

    def test_db_is_empty_on_connect(self):
        engine = self.connect(sqlite3)
        session = Session()
        self.assertEqual(0, session.query(State).count())


class IntialiserTest(Initialiser, unittest.TestCase):

    def test_db_is_initialised_on_connect(self):
        engine = self.connect(sqlite3)
        session = Session()
        nStates = len([s for m in fsms for s in m.values])
        self.assertEqual(nStates, session.query(State).count())
