#!/usr/bin/env python3
# encoding: UTF-8

from cloudhands.common.schema import fsm_factory

CredentialState = fsm_factory(
    "credential", ["untrusted", "trusted", "expired"])

HostState = fsm_factory(
    "host", ["requested", "scheduling", "unknown", "up", "down"])

MembershipState = fsm_factory(
    "membership", ["invite", "active", "expired", "withdrawn"])
#"""{}""".format(' '.join(MembershipState.values))
