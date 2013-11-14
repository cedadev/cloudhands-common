#!/usr/bin/env python3
# encoding: UTF-8

import sqlite3
import unittest

from cloudhands.common.connectors import SQLite3Client
from cloudhands.common.connectors import Session

from cloudhands.common.fsm import MembershipState

import cloudhands.common.schema
from cloudhands.common.schema import EmailAddress
from cloudhands.common.schema import Membership
from cloudhands.common.schema import State
from cloudhands.common.schema import Touch
from cloudhands.common.schema import User

from cloudhands.common.tricks import create_user_grant_email_membership


class TestUserMembership(SQLite3Client, unittest.TestCase):

    def setUp(self):
        """ Every test gets its own in-memory database """
        self.engine = self.connect(sqlite3)
        session = Session()
        session.add_all(
            State(fsm=MembershipState.table, name=v)
            for v in MembershipState.values)
        session.commit()

    def test_quick_add_user(self):
        session = Session()
        session.autoflush = False   # http://stackoverflow.com/a/4202016
        val = "my.name@test.org"
        user = create_user_grant_email_membership(session, val)
        self.assertIs(user, session.query(User).join(Touch).join(
            EmailAddress).filter(EmailAddress.value == val).first())
