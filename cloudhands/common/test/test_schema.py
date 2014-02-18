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
from cloudhands.common.schema import Archive
from cloudhands.common.schema import Directory
from cloudhands.common.schema import Host
from cloudhands.common.schema import IPAddress
from cloudhands.common.schema import Membership
from cloudhands.common.schema import Node
from cloudhands.common.schema import Organisation
from cloudhands.common.schema import Provider
from cloudhands.common.schema import Resource
from cloudhands.common.schema import State
from cloudhands.common.schema import Subscription
from cloudhands.common.schema import Touch
from cloudhands.common.schema import User


class TestSubscriptionState(unittest.TestCase):

    def tearDown(self):
        """ Every test gets its own in-memory database """
        r = Registry()
        r.disconnect(sqlite3, ":memory:")

    def test_duplicate_names(self):
        session = Registry().connect(sqlite3, ":memory:").session
        session.add_all([
            State(fsm="subscription", name="unchecked"),
            State(fsm="subscription", name="unchecked")])
        self.assertRaises(
            sqlalchemy.exc.IntegrityError, session.commit)

    def test_shared_names(self):
        """ State names can be shared across FSMs """
        session = Registry().connect(sqlite3, ":memory:").session
        session.add_all([
            State(fsm="subscription", name="start"),
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
        session.add(Organisation(
            uuid=uuid.uuid4().hex,
            name="TestOrg"))
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
        session.add(Organisation(
            uuid=uuid.uuid4().hex,
            name="TestOrg"))
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
        session.add(Organisation(
            uuid=uuid.uuid4().hex,
            name="TestOrg"))
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


class TestOrganisationsAndProviders(unittest.TestCase):

    def setUp(self):
        """ Populate test database"""
        session = Registry().connect(sqlite3, ":memory:").session
        session.add_all(
            State(fsm=MembershipState.table, name=v)
            for v in MembershipState.values)
        session.add(Organisation(
            uuid=uuid.uuid4().hex,
            name="TestOrg"))
        session.add(Archive(
            name="NITS", uuid=uuid.uuid4().hex))
        session.commit()

    def tearDown(self):
        """ Every test gets its own in-memory database """
        r = Registry()
        r.disconnect(sqlite3, ":memory:")

    def test_organisation_subscribes_to_archive(self):
        session = Registry().connect(sqlite3, ":memory:").session
        archive = session.query(Archive).filter(
            Archive.name == "NITS").first()
        self.assertTrue(archive)
        org = session.query(Organisation).one()
        subs = Subscription(
            uuid=uuid.uuid4().hex,
            model=cloudhands.common.__version__,
            organisation=org, provider=archive)
        session.add(subs)
        session.commit()

        self.assertEqual(
            1, session.query(Subscription, Organisation, Archive).filter(
            Organisation.id == org.id).filter(
            Archive.id == archive.id).count())
        self.assertEqual(1, len(org.subscriptions))

    @unittest.expectedFailure
    def test_organisation_oversubscribes_to_archive(self):
        session = Registry().connect(sqlite3, ":memory:").session
        archive = session.query(Archive).filter(
            Archive.name == "NITS").first()
        self.assertTrue(archive)
        org = session.query(Organisation).one()
        subs = [
            Subscription(
                uuid=uuid.uuid4().hex,
                model=cloudhands.common.__version__,
                organisation=org,
                provider=archive),
            Subscription(
                uuid=uuid.uuid4().hex,
                model=cloudhands.common.__version__,
                organisation=org,
                provider=archive)]
        session.add_all(subs)
        self.assertRaises(
            sqlalchemy.exc.IntegrityError, session.commit)
        session.rollback()
        self.assertEqual(0, len(org.subscriptions))

    def test_organisation_unsubscribes_from_archive(self):
        session = Registry().connect(sqlite3, ":memory:").session
        archive = session.query(Archive).filter(
            Archive.name == "NITS").first()
        self.assertTrue(archive)
        org = session.query(Organisation).one()
        subs = Subscription(
            uuid=uuid.uuid4().hex,
            model=cloudhands.common.__version__,
            organisation=org, provider=archive)
        session.add(subs)
        session.commit()

        session.query(Subscription).filter(
            Subscription.organisation_id == org.id).filter(
            Subscription.provider_id == archive.id).delete()
        session.commit()

        self.assertEqual(
            0, session.query(Subscription, Organisation, Archive).filter(
            Organisation.id == org.id).filter(
            Archive.id == archive.id).count())
        session.rollback()
        self.assertEqual(0, len(org.subscriptions))

    def test_delete_organisation_removes_subscription(self):
        session = Registry().connect(sqlite3, ":memory:").session
        archive = session.query(Archive).filter(
            Archive.name == "NITS").first()
        self.assertTrue(archive)
        org = session.query(Organisation).one()
        subs = Subscription(
            uuid=uuid.uuid4().hex,
            model=cloudhands.common.__version__,
            organisation=org, provider=archive)
        session.add(subs)
        session.commit()
        self.assertEqual(1, len(org.subscriptions))

        session.delete(org)
        session.commit()

        self.assertEqual(0, session.query(Organisation).count())
        self.assertEqual(0, session.query(Subscription).count())


class TestDirectoryResources(unittest.TestCase):

    def setUp(self):
        """ Populate test database"""
        session = Registry().connect(sqlite3, ":memory:").session
        session.add_all(
            State(fsm=MembershipState.table, name=v)
            for v in MembershipState.values)
        session.add(Organisation(
            uuid=uuid.uuid4().hex,
            name="TestOrg"))
        session.add(Archive(
            name="NITS", uuid=uuid.uuid4().hex))
        session.commit()

    def tearDown(self):
        """ Every test gets its own in-memory database """
        r = Registry()
        r.disconnect(sqlite3, ":memory:")

    def test_directory_attaches_to_membership(self):
        session = Registry().connect(sqlite3, ":memory:").session
        session.flush()
        archive = session.query(Archive).filter(
            Archive.name == "NITS").first()
        org = session.query(Organisation).one()
        subs = Subscription(
            uuid=uuid.uuid4().hex,
            model=cloudhands.common.__version__,
            organisation=org, provider=archive)
        user = User(handle=None, uuid=uuid.uuid4().hex)
        session.add_all((subs, user))
        session.commit()

        mship = Membership(
            uuid=uuid.uuid4().hex,
            model=cloudhands.common.__version__,
            organisation=org,
            role="user")
        now = datetime.datetime.utcnow()
        invite = session.query(MembershipState).filter(
            MembershipState.name == "invite").one()
        mship.changes.append(
            Touch(artifact=mship, actor=user, state=invite, at=now))
        session.add(mship)
        session.commit()

        # illustrates user onboarding - membership gets decorated with
        # directory resources
        now = datetime.datetime.utcnow()
        for subs in org.subscriptions:
            if isinstance(subs.provider, Archive):
                d = Directory(
                    description="CEDA data archive",
                    mount_path="/{mount}/panfs/ceda")  # anticipates templating
                latest = mship.changes[-1]
                act = Touch(
                    artifact=mship, actor=user, state=latest.state, at=now)
                d.touch = act
                mship.changes.append(act)
                session.add(d)
                session.commit()

        # Check we can get at the resources from the membership
        self.assertIs(
            d,
            session.query(Resource).join(Touch).join(Membership).filter(
                Membership.id == mship.id).one())


if __name__ == "__main__":
    unittest.main()
