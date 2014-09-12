#!/usr/bin/env python3
# encoding: UTF-8

import uuid

from cloudhands.common.schema import Component
from cloudhands.common.schema import User

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
