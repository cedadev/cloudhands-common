#!/usr/bin/env python3
#   encoding: UTF-8

from collections import namedtuple
import functools

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


class State(Base):
    __tablename__ = "states"

    __table_args__ = (UniqueConstraint("fsm", "name"),)

    id = Column("id", Integer(), nullable=False, primary_key=True)
    fsm = Column("fsm", String(length=32), nullable=False)
    name = Column("name", String(length=64), nullable=False)

    __mapper_args__ = {'polymorphic_on': fsm}


def state_init(class_, fsm, states):
    return class_(fsm=fsm, name=states[0])


def fsm_factory(name, states):
    className = name.capitalize() + "State"
    attribs = dict(
        __mapper_args__={"polymorphic_identity": name},
        table=name,
        values=states,
    )
    class_ = type(className, (State,), attribs)
    class_.init = functools.partial(state_init, class_, name, states)
    return class_

CredentialState = fsm_factory("credential", ["untrusted", "trusted", "expired"])
