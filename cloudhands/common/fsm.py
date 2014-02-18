#!/usr/bin/env python3
# encoding: UTF-8

from cloudhands.common.schema import fsm_factory

HostState = fsm_factory(
    "host", ["requested", "scheduling", "unknown", "up", "down"])

MembershipState = fsm_factory(
    "membership", ["invite", "active", "expired", "withdrawn"])

SubscriptionState = fsm_factory(
    "subscription", ["unchecked", "inactive", "active"])
