#!/usr/bin/env python3
# encoding: UTF-8

import datetime
import uuid

from cloudhands.common.schema import Component
from cloudhands.common.schema import EmailAddress
from cloudhands.common.schema import Registration
from cloudhands.common.schema import Touch
from cloudhands.common.schema import User

from cloudhands.common.states import RegistrationState

def component(session, handle):
    actor = Component(handle=handle, uuid=uuid.uuid4().hex)
    try:
        session.add(actor)
        session.commit()
    except Exception:
        session.rollback()
        session.flush()
    finally:
        return session.query(Component).filter(Component.handle == handle).first()


def user(session, handle, surname=None):
    user = User(handle=handle, surname=surname, uuid=uuid.uuid4().hex)
    try:
        session.add(user)
        session.commit()
    except Exception:
        session.rollback()
        session.flush()
    finally:
        return session.query(User).filter(User.handle == handle).first()


def registration(session, user, email, version):
    unknown = session.query(RegistrationState).filter(
        RegistrationState.name == "pre_registration_person").one()
    reg = Registration(
        uuid=uuid.uuid4().hex,
        model=version)
    now = datetime.datetime.utcnow()
    act = Touch(artifact=reg, actor=user, state=unknown, at=now)
    ea = EmailAddress(touch=act, value=email)
    try:
        session.add(ea)
        session.commit()
    except Exception as e:
        session.rollback()
        reg = None
    finally:
        session.flush()

    return reg
