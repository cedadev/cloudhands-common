#!/usr/bin/env python3
#   encoding: UTF-8

import datetime
import operator
import sqlite3
import unittest
import uuid

import sqlalchemy.exc

from cloudhands.common.connectors import initialise
from cloudhands.common.connectors import Registry

from cloudhands.common.fsm import HostState
from cloudhands.common.fsm import MembershipState

import cloudhands.common.schema
from cloudhands.common.schema import EmailAddress
from cloudhands.common.schema import Host
from cloudhands.common.schema import IPAddress
from cloudhands.common.schema import Membership
from cloudhands.common.schema import Node
from cloudhands.common.schema import Organisation
from cloudhands.common.schema import Provider
from cloudhands.common.schema import Resource
from cloudhands.common.schema import State
from cloudhands.common.schema import Touch
from cloudhands.common.schema import User


class TestCredentialState(unittest.TestCase):

    def tearDown(self):
        """ Every test gets its own in-memory database """
        r = Registry()
        r.disconnect(sqlite3, ":memory:")

    def test_duplicate_names(self):
        session = Registry().connect(sqlite3, ":memory:").session
        session.add_all([
            State(fsm="credential", name="untrusted"),
            State(fsm="credential", name="untrusted")])
        self.assertRaises(
            sqlalchemy.exc.IntegrityError, session.commit)

    def test_shared_names(self):
        """ State names can be shared across FSMs """
        session = Registry().connect(sqlite3, ":memory:").session
        session.add_all([
            State(fsm="credential", name="start"),
            State(fsm="host", name="start")])
        try:
            session.commit()
        except sqlalchemy.exc.IntegrityError as e:
            self.fail(e)


class TestMembership(unittest.TestCase):

    def setUp(self):
        """ Populate test database"""
        session = Registry().connect(sqlite3, ":memory:").session
        session.add_all(
            State(fsm=MembershipState.table, name=v)
            for v in MembershipState.values)
        session.add(Organisation(name="TestOrg"))
        session.commit()

    def tearDown(self):
        """ Every test gets its own in-memory database """
        r = Registry()
        r.disconnect(sqlite3, ":memory:")

    def test_required_field(self):
        session = Registry().connect(sqlite3, ":memory:").session
        org = session.query(Organisation).one()
        mship = Membership(
            uuid=uuid.uuid4().hex,
            model=cloudhands.common.__version__,
            organisation=org)
        session.add(mship)
        self.assertRaises(
            sqlalchemy.exc.IntegrityError, session.commit)

    def test_organisation_field(self):
        session = Registry().connect(sqlite3, ":memory:").session
        org = session.query(Organisation).one()
        mship = Membership(
            uuid=uuid.uuid4().hex,
            model=cloudhands.common.__version__,
            organisation=org,
            role="user")
        session.add(mship)
        session.commit()
        self.assertIs(mship, session.query(Membership).first())
        self.assertIs(org, mship.organisation)


class TestMembershipFSM(unittest.TestCase):

    def setUp(self):
        """ Populate test database"""
        session = Registry().connect(sqlite3, ":memory:").session
        session.add_all(
            State(fsm=MembershipState.table, name=v)
            for v in MembershipState.values)
        session.add(Organisation(name="TestOrg"))
        session.commit()

    def tearDown(self):
        """ Every test gets its own in-memory database """
        r = Registry()
        r.disconnect(sqlite3, ":memory:")

    def test_using_touches(self):
        then = datetime.datetime.utcnow() - datetime.timedelta(seconds=1)
        session = Registry().connect(sqlite3, ":memory:").session

        user = User(handle=None, uuid=uuid.uuid4().hex)
        org = session.query(Organisation).one()

        mship = Membership(
            uuid=uuid.uuid4().hex,
            model=cloudhands.common.__version__,
            organisation=org,
            role="user")
        invite = session.query(MembershipState).filter(
            MembershipState.name == "invite").one()
        mship.changes.append(
            Touch(artifact=mship, actor=user, state=invite, at=then))
        session.add(mship)
        session.commit()

        self.assertIs(mship.changes[0].state, invite)
        self.assertIs(session.query(Touch).first().state, invite)
        self.assertEqual(session.query(Touch).count(), 1)

        now = datetime.datetime.utcnow()
        self.assertTrue(now > then)
        active = session.query(MembershipState).filter(
            MembershipState.name == "active").one()
        mship.changes.append(
            Touch(artifact=mship, actor=user, state=active, at=now))
        session.commit()

        self.assertIs(mship.changes[1].state, active)
        self.assertIs(
            session.query(Touch).order_by(Touch.at)[-1].state, active)
        self.assertEqual(session.query(Touch).count(), 2)

        self.assertEqual(
            session.query(Touch).filter(Touch.at < now).first(),
            mship.changes[0])
        self.assertIs(
            session.query(Touch).filter(
                Touch.at > then).first(),
            mship.changes[1])

        mship.changes.sort(key=operator.attrgetter("at"), reverse=True)

        self.assertEqual(
            session.query(Touch).filter(
                Touch.at < now).first(),
            mship.changes[1])
        self.assertIs(
            session.query(Touch).filter(
                Touch.at > then).first(),
            mship.changes[0])


class TestHostsAndResources(unittest.TestCase):

    def setUp(self):
        """ Populate test database"""
        session = Registry().connect(sqlite3, ":memory:").session
        session.add_all(
            State(fsm=HostState.table, name=v)
            for v in HostState.values)
        session.add(Organisation(name="TestOrg"))
        session.add(Provider(
            name="testcloud.io", uuid=uuid.uuid4().hex))
        session.commit()

    def tearDown(self):
        """ Every test gets its own in-memory database """
        r = Registry()
        r.disconnect(sqlite3, ":memory:")

    def test_single_host_lifecycle(self):
        session = Registry().connect(sqlite3, ":memory:").session

        # 0. Set up User
        user = User(handle="Anon", uuid=uuid.uuid4().hex)

        # 1. User creates a new host
        now = datetime.datetime.utcnow()
        org = session.query(Organisation).one()
        requested = session.query(HostState).filter(
            HostState.name == "requested").one()
        host = Host(
            uuid=uuid.uuid4().hex,
            model=cloudhands.common.__version__,
            organisation=org,
            name="userwantsthishostname"
            )
        host.changes.append(
            Touch(artifact=host, actor=user, state=requested, at=now))
        session.add(host)
        session.commit()

        # 2. Burst controller finds hosts in 'requested' and provisions them
        latest = (h.changes[-1] for h in session.query(Host).all())
        jobs = [(t.actor, t.artifact) for t in latest if t.state is requested]
        self.assertIn((user, host), jobs)

        now = datetime.datetime.utcnow()
        scheduling = session.query(HostState).filter(
            HostState.name == "scheduling").one()
        host.changes.append(
            Touch(artifact=host, actor=user, state=scheduling, at=now))
        session.commit()

        # 3. Burst controller raises a node
        now = datetime.datetime.utcnow()
        provider = session.query(Provider).one()
        act = Touch(artifact=host, actor=user, state=scheduling, at=now)
        host.changes.append(act)
        node = Node(name=host.name, touch=act, provider=provider)
        session.add(node)
        session.commit()

        # 4. Burst controller allocates an IP
        now = datetime.datetime.utcnow()
        act = Touch(artifact=host, actor=user, state=scheduling, at=now)
        host.changes.append(act)
        ip = IPAddress(value="192.168.1.4", touch=act, provider=provider)
        session.add(ip)
        self.assertIn(act, session)
        session.commit()

        # 5. Burst controller marks Host as unknown
        now = datetime.datetime.utcnow()
        unknown = session.query(HostState).filter(
            HostState.name == "unknown").one()
        host.changes.append(
            Touch(artifact=host, actor=user, state=unknown, at=now))

        # 6. Recovering details of provisioning of this host
        resources = [r for i in session.query(Touch).filter(
            Touch.artifact == host).all() for r in i.resources]
        self.assertIn(node, resources)
        self.assertIn(ip, resources)


if __name__ == "__main__":
    unittest.main()
