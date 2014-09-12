#!/usr/bin/env python3
#   encoding: UTF-8

import datetime
import ipaddress
import operator
import sqlite3
import textwrap
import unittest
import uuid

import sqlalchemy.exc

from cloudhands.common.connectors import initialise
from cloudhands.common.connectors import Registry

import cloudhands.common.schema
from cloudhands.common.schema import Appliance
from cloudhands.common.schema import Archive
from cloudhands.common.schema import Component
from cloudhands.common.schema import CatalogueChoice
from cloudhands.common.schema import CatalogueItem
from cloudhands.common.schema import Directory
from cloudhands.common.schema import Host
from cloudhands.common.schema import IPAddress
from cloudhands.common.schema import Label
from cloudhands.common.schema import Membership
from cloudhands.common.schema import Node
from cloudhands.common.schema import Organisation
from cloudhands.common.schema import OSImage
from cloudhands.common.schema import Provider
from cloudhands.common.schema import Registration
from cloudhands.common.schema import Resource
from cloudhands.common.schema import SoftwareDefinedNetwork
from cloudhands.common.schema import State
from cloudhands.common.schema import Subscription
from cloudhands.common.schema import TimeInterval
from cloudhands.common.schema import Touch
from cloudhands.common.schema import User

from cloudhands.common.states import ApplianceState
from cloudhands.common.states import HostState
from cloudhands.common.states import MembershipState
from cloudhands.common.states import RegistrationState
from cloudhands.common.states import SubscriptionState


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


class TestLabel(unittest.TestCase):

    def setUp(self):
        """ Populate test database"""
        session = Registry().connect(sqlite3, ":memory:").session

    def tearDown(self):
        """ Every test gets its own in-memory database """
        r = Registry()
        r.disconnect(sqlite3, ":memory:")

    def test_names_are_not_unique(self):
        session = Registry().connect(sqlite3, ":memory:").session
        session.add_all((
            Label(name="Test", description="Test description"),
            Label(name="Test", description="Test description"),
        ))
        session.commit()
        self.assertEqual(2, session.query(Label).count())
    
    def test_descriptions_may_be_omitted(self):
        session = Registry().connect(sqlite3, ":memory:").session
        session.add_all((
            Label(name="One"),
            Label(name="Two"),
        ))
        session.commit()
        self.assertEqual(2, session.query(Label).count())

        
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


class TestApplianceAndResources(unittest.TestCase):

    def setUp(self):
        """ Populate test database"""
        session = Registry().connect(sqlite3, ":memory:").session
        initialise(session)
        session.add_all((
            Organisation(
                uuid=uuid.uuid4().hex,
                name="TestOrg"),
            Provider(
                uuid=uuid.uuid4().hex,
                name="testcloud.io"),
            )
        )
        session.commit()

        org = session.query(Organisation).one()
        provider = session.query(Provider).one()
        actor = session.query(Component).filter(
            Component.handle == "burst.controller").one()
        active = session.query(SubscriptionState).filter(
            SubscriptionState.name == "active").one()
        subs = Subscription(
            uuid=uuid.uuid4().hex,
            model=cloudhands.common.__version__,
            organisation=org, provider=provider)
        session.add(subs)
        session.commit()

        now = datetime.datetime.utcnow()
        act = Touch(artifact=subs, actor=actor, state=active, at=now)
        net = ipaddress.ip_network("172.16.144.0/29")
        session.add_all(
            (IPAddress(value=str(ip), provider=provider, touch=act)
            for ip in net.hosts()))
        session.commit()

        self.assertEqual(6, session.query(IPAddress).count())

        session.add_all((
            CatalogueItem(
                uuid=uuid.uuid4().hex,
                name="Web Server",
                description="Apache server VM",
                note=None,
                logo=None,
                organisation=org,
            ),
            CatalogueItem(
                uuid=uuid.uuid4().hex,
                name="File Server",
                description="OpenSSH server VM",
                note=None,
                logo=None,
                organisation=org,
            )
        ))
        session.commit()

    def tearDown(self):
        """ Every test gets its own in-memory database """
        r = Registry()
        r.disconnect(sqlite3, ":memory:")

    def test_single_appliance_lifecycle(self):
        session = Registry().connect(sqlite3, ":memory:").session

        # 0. Set up User
        user = User(handle="Anon", uuid=uuid.uuid4().hex)
        org = session.query(Organisation).one()

        # 1. User creates a new appliance
        now = datetime.datetime.utcnow()
        requested = session.query(ApplianceState).filter(
            ApplianceState.name == "requested").one()
        app = Appliance(
            uuid=uuid.uuid4().hex,
            model=cloudhands.common.__version__,
            organisation=org,
            )
        act = Touch(artifact=app, actor=user, state=requested, at=now)

        tmplt = session.query(CatalogueItem).first()
        choice = CatalogueChoice(
            provider=None, touch=act, natrouted=True,
            **{k: getattr(tmplt, k, None)
            for k in ("name", "description", "logo")})
        session.add(choice)
        session.commit()

        self.assertEqual(
            1, session.query(CatalogueChoice).join(Touch).join(Appliance).filter(
            Appliance.id == app.id).count())

        now = datetime.datetime.utcnow()
        configuring = session.query(ApplianceState).filter(
            ApplianceState.name == "configuring").one()
        act = Touch(artifact=app, actor=user, state=configuring, at=now)
        session.add(act)
        session.commit()

        self.assertEqual(
            2, session.query(Touch).join(Appliance).filter(
            Appliance.id == app.id).count())

        # 2. Appliance persists and is configured interactively by user
        latest = app.changes[-1]
        now = datetime.datetime.utcnow()
        act = Touch(
            artifact=app, actor=user, state=latest.state, at=now)
        label = Label(
            name="test_server01",
            description="This is just for kicking tyres",
            touch=act)
        session.add(label)
        session.commit()

        self.assertEqual(
            3, session.query(Touch).join(Appliance).filter(
            Appliance.id == app.id).count())

        # 3. When user is happy, clicks 'Go'
        now = datetime.datetime.utcnow()
        preprovision = session.query(ApplianceState).filter(
            ApplianceState.name == "pre_provision").one()
        act = Touch(
            artifact=app, actor=user, state=preprovision, at=now)
        session.add(act)
        session.commit()

        self.assertEqual(
            4, session.query(Touch).join(Appliance).filter(
            Appliance.id == app.id).count())

        # 4. Burst controller finds hosts in 'pre_provision' and actions them
        latest = (h.changes[-1] for h in session.query(Appliance).all())
        jobs = [
            (t.actor, t.artifact) for t in latest
            if t.state is preprovision]
        self.assertIn((user, app), jobs)

        now = datetime.datetime.utcnow()
        provisioning = session.query(ApplianceState).filter(
            ApplianceState.name == "provisioning").one()
        app.changes.append(
            Touch(artifact=app, actor=user, state=provisioning, at=now))
        session.commit()

        # 5. Burst controller raises a node
        now = datetime.datetime.utcnow()
        provider = session.query(Provider).one()
        act = Touch(artifact=app, actor=user, state=provisioning, at=now)

        label = session.query(Label).join(Touch).join(Appliance).filter(
            Appliance.id == app.id).first()
        node = Node(name=label.name, touch=act, provider=provider)
        sdn = SoftwareDefinedNetwork(name="bridge_routed_external", touch=act)
        session.add_all((sdn, node))
        session.commit()

        # 6. Burst controller allocates an IP
        now = datetime.datetime.utcnow()
        act = Touch(artifact=app, actor=user, state=provisioning, at=now)
        app.changes.append(act)
        ip = IPAddress(value="192.168.1.4", touch=act, provider=provider)
        session.add(ip)
        self.assertIn(act, session)
        session.commit()

        # 7. Burst controller marks Host as pre_operational
        now = datetime.datetime.utcnow()
        preoperational = session.query(ApplianceState).filter(
            ApplianceState.name == "pre_operational").one()
        app.changes.append(
            Touch(artifact=app, actor=user, state=preoperational, at=now))

        # 8. Recovering details of provisioning of this host
        resources = [r for i in session.query(Touch).filter(
            Touch.artifact == app).all() for r in i.resources]
        self.assertIn(node, resources)
        self.assertIn(sdn, resources)
        self.assertIn(ip, resources)


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

    def test_single_host_lifecycle_with_sdn(self):
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
        act = Touch(artifact=host, actor=user, state=requested, at=now)
        osImg = OSImage(name="CentOS 6.5", touch=act)
        host.changes.append(act)
        session.add_all((osImg, host))
        session.commit()

        # 2. Burst controller finds hosts in 'requested' and provisions them
        latest = (h.changes[-1] for h in session.query(Host).all())
        jobs = [(t.actor, t.artifact) for t in latest if t.state is requested]
        self.assertIn((user, host), jobs)

        now = datetime.datetime.utcnow()
        scheduling = session.query(HostState).filter(
            HostState.name == "scheduling").one()
        act = Touch(artifact=host, actor=user, state=scheduling, at=now)
        host.changes.append(act)
        session.commit()

        # 3. Burst controller raises a node
        now = datetime.datetime.utcnow()
        provider = session.query(Provider).one()
        act = Touch(artifact=host, actor=user, state=scheduling, at=now)
        host.changes.append(act)
        node = Node(name=host.name, touch=act, provider=provider)
        sdn = SoftwareDefinedNetwork(name="bridge_routed_external", touch=act)
        session.add_all((sdn, node))
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
        self.assertIn(sdn, resources)
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


class TestCatalogueItem(unittest.TestCase):

    def setUp(self):
        session = Registry().connect(sqlite3, ":memory:").session
        session.add(Organisation(
            name="MARMITE", uuid=uuid.uuid4().hex))
        session.commit()

    def tearDown(self):
        """ Every test gets its own in-memory database """
        r = Registry()
        r.disconnect(sqlite3, ":memory:")

    def test_typical_field_text(self):
        ci = CatalogueItem(
            name="NFS Client",
            description="Headless VM for file transfer operations",
            note=textwrap.dedent("""
                <p>This VM runs CentOS 6.5 with a minimal amount of RAM and
                no X server. It is used for file transfer operations from the
                command line.</p>
                """),
            logo="headless",
        )

    def test_organisation_join(self):
        session = Registry().connect(sqlite3, ":memory:").session
        org = session.query(Organisation).one()
        self.assertEqual(0, session.query(CatalogueItem).count())
        ci = CatalogueItem(
            uuid=uuid.uuid4().hex,
            name="Web Server",
            description="Headless VM with Web server",
            note=textwrap.dedent("""
                <p>This VM runs Apache on CentOS 6.5.
                It has 8GB RAM and 4 CPU cores.
                It is used for hosting websites and applications with a
                Web API.</p>
                """),
            logo="headless",
            organisation=org
        )
        session.add(ci)
        session.commit()
        self.assertEqual(1, session.query(CatalogueItem).join(Organisation).filter(
            Organisation.uuid == org.uuid).count())

    def test_name_unique_across_organisations(self):
        session = Registry().connect(sqlite3, ":memory:").session
        session.add(Organisation(
            name="BRANSTON", uuid=uuid.uuid4().hex))
        session.commit()
        orgs = session.query(Organisation).all()

        session.add_all((
            CatalogueItem(
                name="Blog Server",
                description="WordPress server VM",
                note=None,
                logo=None,
                organisation=orgs[0]
            ),
            CatalogueItem(
                name="Blog Server",
                description="Tumblr server VM",
                note=None,
                logo=None,
                organisation=orgs[1]
            )
        ))

        self.assertRaises(
            sqlalchemy.exc.IntegrityError, session.commit)

    def test_name_unique_within_organisation(self):
        session = Registry().connect(sqlite3, ":memory:").session
        org = session.query(Organisation).one()
        session.add_all((
            CatalogueItem(
                name="Web Server",
                description="Apache web server VM",
                note=None,
                logo=None,
                organisation=org
            ),
            CatalogueItem(
                name="Web Server",
                description="Nginx web server VM",
                note=None,
                logo=None,
                organisation=org
            )
        ))

        self.assertRaises(
            sqlalchemy.exc.IntegrityError, session.commit)


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


class TestTimeInterval(unittest.TestCase):

    def setUp(self):
        """ Populate test database"""
        session = Registry().connect(sqlite3, ":memory:").session
        session.add(
            Component(handle="Async agent", uuid=uuid.uuid4().hex))
        session.add_all(
            State(fsm=RegistrationState.table, name=v)
            for v in RegistrationState.values)
        session.commit()

    def tearDown(self):
        """ Every test gets its own in-memory database """
        r = Registry()
        r.disconnect(sqlite3, ":memory:")

    def test_time_query(self):
        session = Registry().connect(sqlite3, ":memory:").session
        agent = session.query(Component).one()
        state = session.query(MembershipState).first()
        reg = Registration(
            uuid=uuid.uuid4().hex,
            model=cloudhands.common.__version__)
        start = now = datetime.datetime.now()
        then = start + datetime.timedelta(minutes=90)
        end = start + datetime.timedelta(hours=24)
        act = Touch(artifact=reg, actor=agent, state=state, at=now)
        limit = TimeInterval(end=then, touch=act) 
        session.add(limit)
        session.commit()
        self.assertEqual(session.query(TimeInterval).filter(
            TimeInterval.end > now).count(), 1)

        self.assertIs(reg,
            session.query(Registration).join(Touch).join(TimeInterval).filter(
                TimeInterval.end.between(start, end)).first())
        
    
if __name__ == "__main__":
    unittest.main()
