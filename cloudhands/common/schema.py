#!/usr/bin/env python3
#   encoding: UTF-8

from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import ForeignKeyConstraint
from sqlalchemy import String
from sqlalchemy import UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.schema import Table
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
    uuid = Column("uuid", CHAR(length=32), nullable=False)
    name = Column("name", String(length=64), nullable=False, unique=True)

    hosts = relationship("Host")
    memberships = relationship("Membership")
    subscriptions = relationship("Subscription", cascade="all, delete")
    catalogue = relationship("CatalogueItem")


class CatalogueItem(Base):
    """
    This table stores the details of an appliance as advertised to the user.
    """
    __tablename__ = "catalogueitems"

    uuid = Column("uuid", CHAR(length=32), nullable=False)
    name = Column(
        "name", String(length=32),
        nullable=False, primary_key=True, unique=True)
    organisation_id = Column(
        "organisation_id", Integer, ForeignKey("organisations.id"))
    description = Column(
        "description", String(length=64), nullable=False)
    note = Column(
        "note", String(length=1024), nullable=True)
    logo = Column(
        "logo", String(length=32), nullable=True)
    
    organisation = relationship("Organisation")


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


class Appliance(Artifact):
    """
    An Appliance is a computational asset. An appliance is created from an item
    in a catalogue. It is provisioned on one or more nodes, with a configured
    network. The correct data sources must be mounted and the right users given
    access. All this is represented by a Appliance record and its resources.
    """
    __tablename__ = "appliances"

    id = Column("id", Integer, ForeignKey("artifacts.id"),
                nullable=False, primary_key=True)
    organisation_id = Column(
        "organisation_id", Integer, ForeignKey("organisations.id"),
        nullable=False)

    organisation = relationship("Organisation")

    __mapper_args__ = {"polymorphic_identity": "appliance"}


class Membership(Artifact):
    """
    No user may interact with the system without specific membership
    privileges. The user accumulates credentials against a
    membership record. The membership defines the role a user may operate
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
    sources must be mounted and the right users given access. All this is
    represented by a Host record and its resources.
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


class Registration(Artifact):
    """
    No user may interact with the system without having registered.
    The registration is the artifact in use during the onboarding of a
    new user.
    """
    __tablename__ = "registrations"

    id = Column("id", Integer, ForeignKey("artifacts.id"),
                nullable=False, primary_key=True)

    __mapper_args__ = {"polymorphic_identity": "registration"}


class Subscription(Artifact):
    """
    Represents the relationship between an organisation and a provider
    """
    __tablename__ = "subscriptions"

    id = Column("id", Integer, ForeignKey("artifacts.id"),
                nullable=False, primary_key=True)
    organisation_id = Column(
        "organisation_id", Integer, ForeignKey("organisations.id"))
    provider_id = Column("provider_id", Integer, ForeignKey("providers.id"))

    organisation = relationship("Organisation")
    provider = relationship("Provider")

    __mapper_args__ = {"polymorphic_identity": "subscription"}


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


class Provider(Base):
    """
    This is the base table for all providers in the system.

    Providers are created with globally unique `uuids` so their identity can
    be maintained across sharded databases.

    Concrete classes define their own tables according to SQLAlchemy's
    `joined-table inheritance`_.
    """

    __tablename__ = "providers"

    id = Column("id", Integer(), nullable=False, primary_key=True)
    typ = Column("typ", String(length=32), nullable=False)
    uuid = Column("uuid", CHAR(length=32), nullable=False, unique=True)
    name = Column("name", String(length=64), nullable=True, unique=True)

    __mapper_args__ = {
        "polymorphic_identity": "provider",
        "polymorphic_on": typ}


class Archive(Provider):
    __tablename__ = "archives"

    id = Column("id", Integer, ForeignKey("providers.id"),
                nullable=False, primary_key=True)
    name = Column("value", String(length=128), nullable=False, unique=True)

    __mapper_args__ = {"polymorphic_identity": "archive"}


class Cloud(Provider):
    __tablename__ = "clouds"

    id = Column("id", Integer, ForeignKey("providers.id"),
                nullable=False, primary_key=True)
    name = Column("value", String(length=128), nullable=False, unique=True)

    __mapper_args__ = {"polymorphic_identity": "cloud"}


class Resource(Base):
    """
    This is the base table for all resources in the system.

    Resources can have globally unique `uris` if their identity must
    be maintained across sharded databases.

    Some resources have a `provider`. It is common for some resource values
    to be unique within a provider.

    Concrete classes define their own tables according to SQLAlchemy's
    `joined-table inheritance`_.
    """
    __tablename__ = "resources"

    id = Column("id", Integer(), nullable=False, primary_key=True)
    typ = Column("typ", String(length=32), nullable=False)
    provider_id = Column(
        "provider_id", Integer, ForeignKey("providers.id"), nullable=True)
    touch_id = Column("touch_id", Integer, ForeignKey("touches.id"))

    provider = relationship("Provider")
    touch = relationship("Touch")

    __mapper_args__ = {
        "polymorphic_identity": "resource",
        "polymorphic_on": typ}


class BcryptedPassword(Resource):
    """
    This table stores passwords as bcrypt hashes
    """
    __tablename__ = "bcryptedpasswords"

    id = Column("id", Integer, ForeignKey("resources.id"),
                nullable=False, primary_key=True)
    value = Column("value", String(length=60), nullable=False, unique=True)

    __mapper_args__ = {"polymorphic_identity": "bcryptedpassword"}


class CatalogueChoice(Resource):
    """
    This table stores the details of an appliance as the user expects it to
    be provisioned.
    """
    __tablename__ = "cataloguechoices"

    id = Column("id", Integer, ForeignKey("resources.id"),
                nullable=False, primary_key=True)
    name = Column(
        "name", String(length=32), nullable=False, unique=False)
    description = Column(
        "description", String(length=64), nullable=False)
    logo = Column(
        "logo", String(length=32), nullable=True)

    __mapper_args__ = {"polymorphic_identity": "cataloguechoice"}


class Label(Resource):
    """
    This table stores the details of an appliance as the user wants them
    be displayed.
    """
    __tablename__ = "labels"

    id = Column("id", Integer, ForeignKey("resources.id"),
                nullable=False, primary_key=True)
    name = Column(
        "name", String(length=32), nullable=False, unique=True)
    description = Column(
        "description", String(length=64), nullable=False)

    __mapper_args__ = {"polymorphic_identity": "label"}


class Directory(Resource):
    """
    This table stores directory paths.
    """
    __tablename__ = "directories"

    id = Column("id", Integer, ForeignKey("resources.id"),
                nullable=False, primary_key=True)
    description = Column(
        "description", String(length=64), nullable=False)
    mount_path = Column(
        "mount_path", String(length=256), nullable=False, unique=True)

    __mapper_args__ = {"polymorphic_identity": "directory"}


class EmailAddress(Resource):
    """
    This table stores email addresses. They are expected to be unique.
    """
    __tablename__ = "emailaddresses"

    id = Column("id", Integer, ForeignKey("resources.id"),
                nullable=False, primary_key=True)
    value = Column("value", String(length=128), nullable=False, unique=True)

    __mapper_args__ = {"polymorphic_identity": "emailaddress"}


class OSImage(Resource):
    """
    This table stores names of Operating System images.
    They are expected to be unique.
    """
    __tablename__ = "osimages"

    id = Column("id", Integer, ForeignKey("resources.id"),
                nullable=False, primary_key=True)
    name = Column("name", String(length=64), nullable=False, unique=False)

    __mapper_args__ = {"polymorphic_identity": "osimage"}


class SoftwareDefinedNetwork(Resource):
    __tablename__ = "softwaredefinednetworks"

    id = Column("id", Integer, ForeignKey("resources.id"),
                nullable=False, primary_key=True)
    name = Column("name", String(length=32), nullable=False, unique=False)

    __mapper_args__ = {"polymorphic_identity": "softwaredefinednetwork"}


class TimeInterval(Resource):
    __tablename__ = "timeintervals"

    id = Column("id", Integer, ForeignKey("resources.id"),
                nullable=False, primary_key=True)
    end = Column("end", DateTime(), nullable=False)

    __mapper_args__ = {"polymorphic_identity": "timeinterval"}


class IPAddress(Resource):
    """
    An Internet address. The address is stored as a string; no interpretation
    (ie: IPv4, IPv6) is placed on the value.
    """
    __tablename__ = "ipaddresses"

    id = Column("id", Integer, ForeignKey("resources.id"),
                nullable=False, primary_key=True)
    value = Column("value", String(length=64), nullable=False, unique=True)

    __mapper_args__ = {"polymorphic_identity": "ipaddress"}


class Node(Resource):
    """
    Represents a physical server, an instance of a virtual machine (VM),
    root jail, container or other computational resource.
    """
    __tablename__ = "nodes"

    id = Column("id", Integer, ForeignKey("resources.id"),
                nullable=False, primary_key=True)
    name = Column("name", String(length=64), nullable=False)
    uri = Column("uri", String(length=256), nullable=True, unique=True)

    __mapper_args__ = {"polymorphic_identity": "node"}


class PosixUId(Resource):
    """
    The POSIX user name of a user at a particular provider.
    """
    __tablename__ = "posixuids"

    id = Column("id", Integer, ForeignKey("resources.id"),
                nullable=False, primary_key=True)
    value = Column("value", String(length=64), nullable=False)

    __mapper_args__ = {"polymorphic_identity": "posixuid"}


class PosixUIdNumber(Resource):
    """
    The POSIX user id number at a particular provider.
    """
    __tablename__ = "posixuidnumbers"

    id = Column("id", Integer, ForeignKey("resources.id"),
                nullable=False, primary_key=True)
    value = Column("value", Integer, nullable=False)

    __mapper_args__ = {"polymorphic_identity": "posixuidnumber"}


class PosixGId(Resource):
    """
    The POSIX identity of a user group at a particular provider.
    """
    __tablename__ = "posixgids"

    id = Column("id", Integer, ForeignKey("resources.id"),
                nullable=False, primary_key=True)
    value = Column("value", Integer, nullable=False)
    name = Column("name", String(length=64), nullable=True)

    __mapper_args__ = {"polymorphic_identity": "posixgid"}


class PublicKey(Resource):
    """
    A test representation of a public key.
    """
    __tablename__ = "publickeys"

    id = Column("id", Integer, ForeignKey("resources.id"),
                nullable=False, primary_key=True)
    value = Column("value", String(length=512), nullable=False)

    __mapper_args__ = {"polymorphic_identity": "publickey"}


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
