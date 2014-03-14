#!/usr/bin/env python3
# encoding: UTF-8

from cloudhands.common.schema import fsm_factory

HostState = fsm_factory(
    "host", ["requested", "scheduling", "unknown", "up", "deleting", "down"])

MembershipState = fsm_factory(
    "membership", ["invite", "active", "expired", "withdrawn"])

RegistrationState = fsm_factory(
    "registration", ["prepass", "valid", "expired", "withdrawn"])

SubscriptionState = fsm_factory(
    "subscription", ["maintenance", "unchecked", "inactive", "active"])
