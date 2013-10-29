#!/usr/bin/env python3
#   encoding: UTF-8

import sqlalchemy
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from cloudhands.common.schema import metadata

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
