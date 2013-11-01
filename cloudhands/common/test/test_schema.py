#!/usr/bin/env python3
#   encoding: UTF-8

import datetime
import operator
import sqlite3
import unittest
import uuid

import sqlalchemy.exc

from cloudhands.common.connectors import SQLite3Client
from cloudhands.common.connectors import Session

from cloudhands.common.fsm import CredentialState

import cloudhands.common.schema
from cloudhands.common.schema import EmailCredential
from cloudhands.common.schema import State
from cloudhands.common.schema import Touch
from cloudhands.common.schema import User


class TestCredentialState(SQLite3Client, unittest.TestCase):

    def setUp(self):
        """ Every test gets its own in-memory database """
        self.engine = self.connect(sqlite3)

    def test_duplicate_names(self):
        session = Session()
        session.add_all([
            State(fsm="credential", name="untrusted"),
            State(fsm="credential", name="untrusted")])
        self.assertRaises(
            sqlalchemy.exc.IntegrityError, session.commit)

    def test_shared_names(self):
        """ State names can be shared across FSMs """
        session = Session()
        session.add_all([
            State(fsm="credential", name="start"),
            State(fsm="billing", name="start")])
        try:
            session.commit()
        except sqlalchemy.exc.IntegrityError as e:
            self.fail(e)


class TestEmailCredential(SQLite3Client, unittest.TestCase):

    def setUp(self):
        """ Every test gets its own in-memory database """
        self.engine = self.connect(sqlite3)

    def test_required_field(self):
        session = Session()
        cred = EmailCredential(
            typ="emailcredential", uuid=uuid.uuid4().hex,
            model=cloudhands.common.__version__)
        session.add(cred)
        self.assertRaises(
            sqlalchemy.exc.IntegrityError, session.commit)

    def test_email_field(self):
        session = Session()
        cred = EmailCredential(
            typ="emailcredential", uuid=uuid.uuid4().hex,
            model=cloudhands.common.__version__,
            email="somebody@gmail.com")
        session.add(cred)
        session.commit()
        self.assertIs(cred, session.query(EmailCredential).first())


class TestEmailCredentialFSM(SQLite3Client, unittest.TestCase):

    def setUp(self):
        """ Every test gets its own in-memory database """
        self.engine = self.connect(sqlite3)
        session = Session()
        session.add_all(
            State(fsm=CredentialState.table, name=v)
            for v in CredentialState.values)
        session.commit()

    def test_using_touches(self):
        then = datetime.datetime.utcnow() - datetime.timedelta(seconds=1)
        session = Session()

        user = User(handle="Anon", uuid=uuid.uuid4().hex)

        cred = EmailCredential(
            typ="emailcredential", uuid=uuid.uuid4().hex,
            model=cloudhands.common.__version__,
            email="somebody@gmail.com")
        untrust = session.query(CredentialState).filter(
            CredentialState.name == "untrusted").first()
        cred.changes.append(
            Touch(artifact=cred, actor=user, state=untrust, at=then))
        session.add(cred)
        session.commit()

        self.assertIs(cred.changes[0].state, untrust)
        self.assertIs(session.query(Touch).first().state, untrust)
        self.assertEqual(session.query(Touch).count(), 1)

        now = datetime.datetime.utcnow()
        self.assertTrue(now > then)
        trust = session.query(CredentialState).filter(
            CredentialState.name == "trusted").first()
        cred.changes.append(
            Touch(artifact=cred, actor=user, state=trust, at=now))
        session.commit()

        self.assertIs(cred.changes[1].state, trust)
        self.assertIs(
            session.query(Touch).order_by(Touch.at)[-1].state, trust)
        self.assertEqual(session.query(Touch).count(), 2)

        self.assertEqual(
            session.query(Touch).filter(Touch.at < now).first(),
            cred.changes[0])
        self.assertIs(
            session.query(Touch).filter(
                Touch.at > then).first(),
            cred.changes[1])

        cred.changes.sort(key=operator.attrgetter("at"), reverse=True)

        self.assertEqual(
            session.query(Touch).filter(
                Touch.at < now).first(),
            cred.changes[1])
        self.assertIs(
            session.query(Touch).filter(
                Touch.at > then).first(),
            cred.changes[0])

if __name__ == "__main__":
    unittest.main()