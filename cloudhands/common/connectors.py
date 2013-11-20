#!/usr/bin/env python3
#   encoding: UTF-8

from collections import namedtuple
from itertools import chain
import logging
import sqlite3
import uuid

import sqlalchemy
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from cloudhands.common.component import burstCtrl  # TODO: Entry point
from cloudhands.common.discovery import fsms

from cloudhands.common.schema import metadata
from cloudhands.common.schema import Component
from cloudhands.common.schema import State

Connection = namedtuple("Connection", ["module", "path", "engine", "session"])

class SQLite3Connector(object):
    """
    A functor which sets up a SQLALchemy connection to a SQLite3 database.
    """

    @staticmethod
    def sqlite_fk_pragma(dbapi_con, con_record):
        dbapi_con.execute("pragma foreign_keys=ON")

    @staticmethod
    def on_connect(dbapi_con, con_record):
        SQLite3Connector.sqlite_fk_pragma(dbapi_con, con_record)

    def __call__(self, module, path):
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
        return engine


class Registry(object):

    _shared_state = {}

    connectors = {
        sqlite3: SQLite3Connector,
    }

    def __init__(self):
        self.__dict__ = self._shared_state
        if not hasattr(self, "_engines"):
            self._engines = {}

    @property
    def items(self):
        return self._engines.keys()

    def connect(self, module, path):
        if (module, path) not in self._engines:
            connector = self.connectors[module]()
            self._engines[(module, path)] = connector(module, path)
        engine = self._engines[(module, path)]
        session = sessionmaker(bind=engine)(autoflush=False)
        return Connection(module, path, engine, session)

    def disconnect(self, module, path):
        engine = self._engines.pop((module, path), None)
        return Connection(module, path, engine, None)


def initialise(session):
    log = logging.getLogger("cloudhands.common.initialise")
    items = chain(
        (State(fsm=m.table, name=s) for m in fsms for s in m.values),
        (Component(uuid=uuid.uuid4().hex, handle=i) for i in (burstCtrl,))
        )
    n = 0
    for i in items:  # Add them individually to permit schema changes
        try:
            session.add(i)
            session.commit()
            n += 1
        except Exception as e:
            session.rollback()
            log.debug(e)
    return n
