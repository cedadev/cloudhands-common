#!/usr/bin/env python3
#   encoding: UTF-8

from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.types import CHAR
from sqlalchemy.orm import relationship

Base = declarative_base()
metadata = Base.metadata


__doc__ = """
The schema module defines tables in the common database
"""


class Artifact(Base):
    __tablename__ = "artifacts"

    id = Column("id", Integer(), nullable=False, primary_key=True)
    typ = Column("typ", String(length=32), nullable=False)
    uuid = Column("uuid", CHAR(length=32), nullable=False)
    model = Column("model", String(length=32), nullable=False)
    changes = relationship("Touch")

    __mapper_args__ = {
        "polymorphic_identity": "artifact",
        "polymorphic_on": typ}


class EmailCredential(Artifact):
    __tablename__ = "emailcredentials"

    id = Column("id", Integer, ForeignKey("artifacts.id"),
                nullable=False, primary_key=True)
    email = Column("email", String(length=128), nullable=False, unique=True)

    __mapper_args__ = {"polymorphic_identity": "emailcredential"}


class Actor(Base):
    """
    This is the base table for all actors in the system. Concrete classes
    define their own tables according to SQLAlchemy's
    `joined-table inheritance`_.

    .. _joined-table inheritance: http://docs.sqlalchemy.org/en/latest/orm\
/inheritance.html#joined-table-inheritance
    """

    __tablename__ = "actors"

    id = Column("id", Integer(), nullable=False, primary_key=True)
    typ = Column("typ", String(length=32), nullable=False)
    uuid = Column("uuid", CHAR(length=32), nullable=False, unique=True)
    handle = Column("handle", String(length=64), nullable=True, unique=True)

    __mapper_args__ = {
        "polymorphic_identity": "actor",
        "polymorphic_on": typ}


class User(Actor):
    __tablename__ = "users"

    id = Column("id", Integer, ForeignKey("actors.id"),
                nullable=False, primary_key=True)

    __mapper_args__ = {"polymorphic_identity": "user"}


class Touch(Base):
    __tablename__ = "touches"

    id = Column("id", Integer(), nullable=False, primary_key=True)
    artifact_id = Column("artifact_id", Integer, ForeignKey("artifacts.id"))
    actor_id = Column("actor_id", Integer, ForeignKey("actors.id"))
    state_id = Column("state_id", Integer, ForeignKey("states.id"))
    at = Column("at", DateTime(), nullable=False)

    artifact = relationship("Artifact")
    actor = relationship("Actor")
    state = relationship("State")


class State(Base):
    """
    State machines which persist their state in the database declare themselves
    using this table.
    """
    __tablename__ = "states"

    __table_args__ = (UniqueConstraint("fsm", "name"),)

    id = Column("id", Integer(), nullable=False, primary_key=True)
    fsm = Column("fsm", String(length=32), nullable=False)
    name = Column("name", String(length=64), nullable=False)

    __mapper_args__ = {'polymorphic_on': fsm}


def fsm_factory(name, states):
    """
    Dynamically create a class for a state machine. The pattern used
    is SQLAlchemy's `single table inheritance`_.

    .. _single table inheritance: http://docs.sqlalchemy.org/en/latest/orm\
/inheritance.html#single-table-inheritance
    """
    className = name.capitalize() + "State"
    attribs = dict(
        __mapper_args__={"polymorphic_identity": name},
        table=name,
        values=states,
    )
    class_ = type(className, (State,), attribs)
    return class_

CredentialState = fsm_factory(
    "credential", ["untrusted", "trusted", "expired"])
