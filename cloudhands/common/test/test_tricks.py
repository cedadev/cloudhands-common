#!/usr/bin/env python3
# encoding: UTF-8

import datetime
import sqlite3
import unittest
import uuid

from cloudhands.common.connectors import SQLite3Client
from cloudhands.common.connectors import Session

from cloudhands.common.fsm import HostState
from cloudhands.common.fsm import MembershipState

import cloudhands.common.schema
from cloudhands.common.schema import EmailAddress
from cloudhands.common.schema import Host
from cloudhands.common.schema import IPAddress
from cloudhands.common.schema import Membership
from cloudhands.common.schema import Organisation
from cloudhands.common.schema import State
from cloudhands.common.schema import Touch
from cloudhands.common.schema import User

from cloudhands.common.tricks import allocate_ip
from cloudhands.common.tricks import create_user_grant_email_membership
from cloudhands.common.tricks import handle_from_email

class TestUserMembership(SQLite3Client, unittest.TestCase):

    def setUp(self):
        """ Every test gets its own in-memory database """
        self.engine = self.connect(sqlite3, ":memory:")
        session = Session()
        session.add_all(
            State(fsm=MembershipState.table, name=v)
            for v in MembershipState.values)
        session.add(Organisation(name="TestOrg"))
        session.commit()

    def test_quick_add_user(self):
        session = Session()
        session.autoflush = False   # http://stackoverflow.com/a/4202016
        oName = "TestOrg"
        eAddr = "my.name@test.org"

        org = session.query(
            Organisation).filter(Organisation.name == oName).one()
        handle = handle_from_email(eAddr)
        user = create_user_grant_email_membership(session, org, eAddr, handle)
        self.assertIs(user, session.query(User).join(Touch).join(
            EmailAddress).filter(EmailAddress.value == eAddr).first())

    def test_add_duplicate_user(self):
        session = Session()
        session.autoflush = False   # http://stackoverflow.com/a/4202016
        oName = "TestOrg"
        eAddr = "my.name@test.org"

        org = session.query(
            Organisation).filter(Organisation.name == oName).one()
        handle = handle_from_email(eAddr)
        user = create_user_grant_email_membership(session, org, eAddr, handle)
        self.assertIsNone(create_user_grant_email_membership(
            session, org, eAddr, handle))

class TestResourceManagement(SQLite3Client, unittest.TestCase):

    def setUp(self):
        """ Every test gets its own in-memory database """
        self.engine = self.connect(sqlite3, ":memory:")
        session = Session()
        session.add_all(
            State(fsm=HostState.table, name=v)
            for v in HostState.values)
        session.add_all(
            State(fsm=MembershipState.table, name=v)
            for v in MembershipState.values)
        session.add(Organisation(name="TestOrg"))
        session.commit()

    def test_reallocate_ip(self):
        session = Session()
        session.autoflush = False   # http://stackoverflow.com/a/4202016
        oName = "TestOrg"
        eAddr = "my.name@test.org"
        hName = "mynode.test.org"
        ipAddr = "192.168.1.1"

        org = session.query(
            Organisation).filter(Organisation.name == oName).one()
        handle = handle_from_email(eAddr)
        user = create_user_grant_email_membership(session, org, eAddr, handle)

        scheduling = session.query(HostState).filter(
            HostState.name == "scheduling").one()
        up = session.query(HostState).filter(
            HostState.name == "up").one()
        hosts = [
            Host(
                uuid=uuid.uuid4().hex,
                model=cloudhands.common.__version__,
                organisation=org,
                name=hName),
            Host(
                uuid=uuid.uuid4().hex,
                model=cloudhands.common.__version__,
                organisation=org,
                name=hName),
        ]
        now = datetime.datetime.utcnow()
        hosts[0].changes.append(
            Touch(artifact=hosts[0], actor=user, state=up, at=now))
        hosts[1].changes.append(
            Touch(artifact=hosts[1], actor=user, state=scheduling, at=now))
        session.add_all(hosts)
        session.commit()

        ip = allocate_ip(session, hosts[0], ipAddr)
        self.assertIn(ip, [r for c in hosts[0].changes for r in c.resources])

        ip = allocate_ip(session, hosts[1], ipAddr)
        self.assertNotIn(
            ip, [r for c in hosts[0].changes for r in c.resources])
        self.assertIn(ip, [r for c in hosts[1].changes for r in c.resources])
