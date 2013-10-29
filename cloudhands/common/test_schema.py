#!/usr/bin/env python3
#   encoding: UTF-8

import datetime
import unittest
import sqlite3

import sqlalchemy
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from cloudhands.common.schema import metadata
from cloudhands.common.schema import CredentialState
from cloudhands.common.schema import EmailCredential
from cloudhands.common.schema import State

Session = sessionmaker()

class SQLite3Client(object):
    """
    A mixin class which sets up a connection to a SQLite3 database
    and binds it through SQLAlchemy to this module's Session class.
    """

    @staticmethod
    def sqlite_fk_pragma(dbapi_con, con_record):
        dbapi_con.execute("pragma foreign_keys=ON")

    @staticmethod
    def on_connect(dbapi_con, con_record):
        SQLite3Client.sqlite_fk_pragma(dbapi_con, con_record)

    def connect(self, module, path=":memory:"):
        """
        Creates, configures and returns a SQLAlchemy engine connected
        to a SQLite3 database.
        """
        #TODO: use sqlalchemy.engine.url.URL
        sqlaPath = "sqlite:///" + path
        engine = sqlalchemy.create_engine(
                    sqlaPath, module=module, poolclass=StaticPool,
                    connect_args={"check_same_thread": False})
        sqlalchemy.event.listen(engine, "connect", self.on_connect)
        metadata.bind = engine
        metadata.create_all()
        Session.configure(bind=engine)
        return engine


class TestCredentialState(SQLite3Client, unittest.TestCase):

    def setUp(self):
        """ Every test gets its own in-memory database """
        self.engine = self.connect(sqlite3)

    def test_initialisation(self):
        obj = CredentialState.init()
        self.assertEqual(CredentialState.table, obj.fsm)
        self.assertEqual(CredentialState.values[0], obj.name)


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


class TestEmailCredentialFSM(SQLite3Client, unittest.TestCase):

    def setUp(self):
        """ Every test gets its own in-memory database """
        self.engine = self.connect(sqlite3)


    def test_create(self):
        session = Session()
        self.assertRaises(TypeError, EmailCredential.init)

    def test_transitions(self):
        cred = EmailCredential.init("somebody@gmail.com")

    def test_new_touch(self):
        then = datetime.datetime.utcnow() - datetime.timedelta(seconds=1)
        session = Session()
        u = User(
            handle="Anon", email="anonymous@gmail.com",
            uuid=uuid.uuid4().hex)
        start = State(fsm="lifecycle", name="start")
        stop = State(fsm="lifecycle", name="stop")
        f = Pricing(
            name="standard", value=5, currency="GBP",
            commission_num=1, commission_den=1,
            description="description")
        p = Product(
            typ="product", uuid=uuid.uuid4().hex,
            model=topicmob.schema.__version__,
            title="title", description="descr", min=4, max=10,
            fee=f)
        p.changes.append(
            Touch(artifact=p, actor=u, state=start, at=then))
        session.add(p)
        session.commit()

        self.assertIs(p.changes[0].state, start)
        self.assertIs(session.query(Touch).first().state, start)
        self.assertEqual(session.query(Touch).count(), 1)

        now = datetime.datetime.utcnow()
        self.assertTrue(now > then)
        p.changes.append(
            Touch(artifact=p, actor=u, state=stop, at=now))
        session.commit()

        self.assertIs(p.changes[1].state, stop)
        self.assertIs(
            session.query(Touch).order_by(Touch.at)[-1].state, stop)
        self.assertEqual(session.query(Touch).count(), 2)

        self.assertEqual(
            session.query(Touch).filter(Touch.at < now).first(),
            p.changes[0])
        self.assertIs(
            session.query(Touch).filter(
                Touch.at > then).first(),
            p.changes[1])

        p.changes.sort(key=operator.attrgetter("at"), reverse=True)

        self.assertEqual(
            session.query(Touch).filter(
                Touch.at < now).first(),
            p.changes[1])
        self.assertIs(
            session.query(Touch).filter(
                Touch.at > then).first(),
            p.changes[0])

if __name__ == "__main__":
    unittest.main()
