#!/usr/bin/env python3
#   encoding: UTF-8

import datetime
import operator
import sqlite3
import unittest
import uuid

import cloudhands.common

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

    def test_using_touches(self):
        then = datetime.datetime.utcnow() - datetime.timedelta(seconds=1)
        session = Registry().connect(sqlite3, ":memory:").session

        user = User(handle=None, uuid=uuid.uuid4().hex)

        reg = Registration(
            uuid=uuid.uuid4().hex,
            model=cloudhands.common.__version__)

        preconfirm = session.query(RegistrationState).filter(
            RegistrationState.name == "preconfirm").one()
        reg.changes.append(
            Touch(artifact=reg, actor=user, state=preconfirm, at=then))
        session.add(reg)
        session.commit()

        self.assertIs(reg.changes[0].state, preconfirm)
        self.assertIs(session.query(Touch).first().state, preconfirm)
        self.assertEqual(session.query(Touch).count(), 1)

        now = datetime.datetime.utcnow()
        self.assertTrue(now > then)
        valid = session.query(RegistrationState).filter(
            RegistrationState.name == "valid").one()
        act = Touch(artifact=reg, actor=user, state=valid, at=now)
        reg.changes.append(act)
        hash = BcryptedPassword(value="a" * 60, touch=act, provider=None)
        session.add(hash)
        session.commit()

        self.assertIs(reg.changes[1].state, valid)
        self.assertIs(
            session.query(Touch).order_by(Touch.at)[-1].state, valid)
        self.assertEqual(session.query(Touch).count(), 2)

        self.assertEqual(
            session.query(Touch).filter(Touch.at < now).first(),
            reg.changes[0])
        self.assertIs(
            session.query(Touch).filter(
                Touch.at > then).first(),
            reg.changes[1])

        reg.changes.sort(key=operator.attrgetter("at"), reverse=True)

        self.assertEqual(
            session.query(Touch).filter(
                Touch.at < now).first(),
            reg.changes[1])
        self.assertIs(
            session.query(Touch).filter(
                Touch.at > then).first(),
            reg.changes[0])

