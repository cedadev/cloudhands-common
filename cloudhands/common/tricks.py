#!/usr/bin/env python3
#   encoding: UTF-8

import datetime
import logging
import uuid

from cloudhands.common.fsm import MembershipState

import cloudhands.common.schema
from cloudhands.common.schema import EmailAddress
from cloudhands.common.schema import Host
from cloudhands.common.schema import IPAddress
from cloudhands.common.schema import Membership
from cloudhands.common.schema import Resource
from cloudhands.common.schema import State
from cloudhands.common.schema import Touch
from cloudhands.common.schema import User

__doc__ = """
Common functions for interacting with the schema.
"""

def handle_from_email(addrVal):
    return ' '.join(
        i.capitalize() for i in addrVal.split('@')[0].split('.'))

def create_user_grant_email_membership(
    session, org, addrVal, handle, role="user"):
    """
    Creates a new user account from an email address. The sequence of
    operations is:

    1.  Add a new Membership record.
    2.  Find or create a User record.
    3.  Touch the membership with an EmailAddress resource from the user.
        The state of membership is set to `granted`.

    :param object session:  A SQLALchemy database session.
    :param Organisation org:    The organisation to join.
    :param string addrVal:   The user's email address.
    :param string handle:   Becomes the user's handle. If not supplied, 
                            handle is constructed from the `addrVal`.
    :param string role: Membership role.
    :returns: The newly created User object.
    """
    log = logging.getLogger("cloudhands.common.tricks")

    # 1.
    mship = Membership(
        uuid=uuid.uuid4().hex,
        model=cloudhands.common.__version__,
        organisation=org,
        role=role)
    try:
        session.add(mship)
        session.commit()
    except Exception as e:
        session.rollback()
        log.warning("Membership '{}:{}' exists".format(org.name, role))

    # 2.
    user = User(handle=handle, uuid=uuid.uuid4().hex)
    try:
        session.add(user)
        session.commit()
    except Exception as e:
        session.rollback()
        log.warning("User with handle '{}' exists".format(handle))
        return None

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

def allocate_ip(session, host, ipAddr):
    owner = session.query(Host).join(Touch).join(IPAddress).filter(
        IPAddress.value == ipAddr).first()
    if owner:
        ip = session.query(IPAddress).filter(IPAddress.value == ipAddr).one()
        owner.resources.remove(ip)
    now = datetime.datetime.utcnow()
    recent = host.changes[-1]
    act = Touch(artifact=host, actor=recent.actor, state=recent.state, at=now)
    host.changes.append(act)
    ip = IPAddress(value=ipAddr, touch=act)
    session.add(ip)
    session.commit()
    return ip
