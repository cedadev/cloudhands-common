#!/usr/bin/env python3
#   encoding: UTF-8

import datetime
import logging
import uuid

from cloudhands.common.fsm import MembershipState

import cloudhands.common.schema
from cloudhands.common.schema import EmailAddress
from cloudhands.common.schema import Membership
from cloudhands.common.schema import Resource
from cloudhands.common.schema import State
from cloudhands.common.schema import Touch
from cloudhands.common.schema import User

__doc__ = """
Common functions for interacting with the schema.
"""

def create_user_grant_email_membership(
    session, addrVal, handle=None, org=None, role="user"):
    """
    Creates a new user account from an email address. The sequence of
    operations is:

    1.  Create a User record.
    2.  Add a new Membership record.
    3.  Touch the membership with an EmailAddress resource from the user.
        The state of membership is set to `granted`.

    :param session:  A SQLALchemy database session.
    :param string addrVal:   The user's email address.
    :param string handle:   Becomes the user's handle. If not supplied, 
                            handle is constructed from the `addrVal`.
    :param string org: Membership organisation.
    :param string role: Membership role.
    :returns: The newly created User object.
    """

    # 1.
    handle = handle or ' '.join(
        i.capitalize() for i in addrVal.split('@')[0].split('.'))
    user = User(handle=handle, uuid=uuid.uuid4().hex)

    # 2.
    mship = Membership(
        uuid=uuid.uuid4().hex,
        model=cloudhands.common.__version__,
        organisation=org,
        role=role)
    session.add(mship)
    session.commit()

    # 3.
    granted = session.query(
        MembershipState).filter(MembershipState.name == "granted").one()
    now = datetime.datetime.utcnow()

    grant = Touch(artifact=mship, actor=user, state=granted, at=now)
    mship.changes.append(grant)
    ea = EmailAddress(value=addrVal, touch=grant)
    session.add(ea)
    session.commit()
    return user
