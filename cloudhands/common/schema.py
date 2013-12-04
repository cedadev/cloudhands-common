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


class Organisation(Base):
    __tablename__ = "organisations"

    id = Column("id", Integer, nullable=False, primary_key=True)
    name = Column("name", String(length=64), nullable=False, unique=True)

    hosts = relationship("Host")
    memberships = relationship("Membership")


class Artifact(Base):
    """
    This is the base table for all artifacts (products) of the system.

    Artifacts are created with globally unique `uuids` so their identity can
    be maintained across sharded databases.

    Concrete classes define their own tables according to SQLAlchemy's
    `joined-table inheritance`_.

    """
    __tablename__ = "artifacts"

    id = Column("id", Integer(), nullable=False, primary_key=True)
    typ = Column("typ", String(length=32), nullable=False)
    uuid = Column("uuid", CHAR(length=32), nullable=False)
    model = Column("model", String(length=32), nullable=False)
    changes = relationship("Touch", order_by="Touch.at")

    __mapper_args__ = {
        "polymorphic_identity": "artifact",
        "polymorphic_on": typ}


# TODO: revisit
class DCStatus(Artifact):
    __tablename__ = "dcstatus"

    id = Column("id", Integer, ForeignKey("artifacts.id"),
                nullable=False, primary_key=True)
    uri = Column("uri", String(length=128), nullable=False)
    name = Column("name", String(length=128), nullable=False)

    __mapper_args__ = {"polymorphic_identity": "dcstatus"}


class Membership(Artifact):
    """
    No user may interact with the system without specific membership
    privileges. The user account accumulates credentials against a
    membership object. The membership defines the role a user may operate
    within an `organisation`.
    """
    __tablename__ = "memberships"

    id = Column("id", Integer, ForeignKey("artifacts.id"),
                nullable=False, primary_key=True)
    organisation_id = Column(
        "organisation_id", Integer, ForeignKey("organisations.id"),
        nullable=False)
    role = Column("role", String(length=32), nullable=False)

    organisation = relationship("Organisation")

    __mapper_args__ = {"polymorphic_identity": "membership"}


class Host(Artifact):
    """
    A Host is a computational asset. To be useful, a host must be sited on a
    functioning node, with a configured network. It must be installed with a
    particular operating system and software packages. The correct data
    sources must be mounted and the right users given access.
    """
    __tablename__ = "hosts"

    id = Column("id", Integer, ForeignKey("artifacts.id"),
                nullable=False, primary_key=True)
    organisation_id = Column(
        "organisation_id", Integer, ForeignKey("organisations.id"),
        nullable=False)
    name = Column("name", String(length=128), nullable=False)

    organisation = relationship("Organisation")

    __mapper_args__ = {"polymorphic_identity": "host"}


class Actor(Base):
    """
    This is the base table for all actors in the system.

    Actors are created with globally unique `uuids` so their identity can
    be maintained across sharded databases.

    Concrete classes define their own tables according to SQLAlchemy's
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
    """
    Stores human users of the system.
    """
    __tablename__ = "users"

    id = Column("id", Integer, ForeignKey("actors.id"),
                nullable=False, primary_key=True)

    __mapper_args__ = {"polymorphic_identity": "user"}


class Component(Actor):
    """
    A registry for those parts of the system which take autonomous action.
    """
    __tablename__ = "components"

    id = Column("id", Integer, ForeignKey("actors.id"),
                nullable=False, primary_key=True)

    __mapper_args__ = {"polymorphic_identity": "component"}


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
    resources = relationship("Resource", cascade="all, delete-orphan")


class Resource(Base):
    """
    This is the base table for all resources in the system.

    Resources are created with globally unique `uris` so their identity can
    be maintained across sharded databases.

    Every resource has a `provider`.

    Concrete classes define their own tables according to SQLAlchemy's
    `joined-table inheritance`_.
    """
    __tablename__ = "resources"

    id = Column("id", Integer, ForeignKey("touches.id"), primary_key=True)
    typ = Column("typ", String(length=32), nullable=False)
    provider = Column("provider", String(length=32), nullable=False)
    uri = Column("uri", String(length=128), nullable=True, unique=True)
    touch = relationship("Touch")

    __mapper_args__ = {
        "polymorphic_identity": "resource",
        "polymorphic_on": typ}


class EmailAddress(Resource):
    __tablename__ = "emailaddresses"

    id = Column("id", Integer, ForeignKey("resources.id"),
                nullable=False, primary_key=True)
    value = Column("value", String(length=128), nullable=False, unique=True)

    __mapper_args__ = {"polymorphic_identity": "emailaddress"}


class IPAddress(Resource):
    __tablename__ = "ipaddresses"

    id = Column("id", Integer, ForeignKey("resources.id"),
                nullable=False, primary_key=True)
    value = Column("value", String(length=64), nullable=False, unique=True)

    __mapper_args__ = {"polymorphic_identity": "ipaddress"}


class Node(Resource):
    __tablename__ = "nodes"

    id = Column("id", Integer, ForeignKey("resources.id"),
                nullable=False, primary_key=True)
    name = Column("name", String(length=64), nullable=False)

    __mapper_args__ = {"polymorphic_identity": "node"}


class Serializable(object):

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class State(Base, Serializable):
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
