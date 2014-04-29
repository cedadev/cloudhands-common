#!/usr/bin/env python3
# encoding: UTF-8

from cloudhands.common.schema import fsm_factory

HostState = fsm_factory(
    "host", ["requested", "scheduling", "unknown", "up", "deleting", "down"])

MembershipState = fsm_factory(
    "membership", ["invite", "active", "expired", "withdrawn"])

RegistrationState = fsm_factory(
    "registration", ["modified", "preconfirm", "postconfirm", "valid", "expired", "withdrawn"])

RegistrationState = fsm_factory(
    "registration", [
        "pre_registration_person",
        "pre_registration_inetorgperson",
        "pre_registration_inetorgperson_sn",
        "pre_user_inetorgperson_dn",
        "pre_user_posixaccount",
        "pre_user_ldappublickey",
])

SubscriptionState = fsm_factory(
    "subscription", ["maintenance", "unchecked", "inactive", "active"])
