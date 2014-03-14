#!/usr/bin/env python3
#   encoding: UTF-8

import datetime
import sqlite3
import unittest
import uuid

from cloudhands.common.connectors import initialise
from cloudhands.common.connectors import Registry

from cloudhands.common.fsm import RegistrationState

from cloudhands.common.schema import BcryptedPassword
from cloudhands.common.schema import Registration
from cloudhands.common.schema import State
from cloudhands.common.schema import Touch
from cloudhands.common.schema import User

class RegistrationTests(unittest.TestCase):

    def setUp(self):
        """ Populate test database"""
        session = Registry().connect(sqlite3, ":memory:").session
        session.add_all(
            State(fsm=RegistrationState.table, name=v)
            for v in RegistrationState.values)
        session.commit()

    def tearDown(self):
        """ Every test gets its own in-memory database """
        r = Registry()
        r.disconnect(sqlite3, ":memory:")

    def test_fisrst(self):
        self.fail()
