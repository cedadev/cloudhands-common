#!/usr/bin/env python3
# encoding: UTF-8

from cloudhands.common.schema import fsm_factory


AccessState = fsm_factory(
    "access", [
        "created",
        "invited",
        "accepted",
        "active",
        "expired",
        "withdrawn"
    ])


ApplianceState = fsm_factory(
    "appliance", [
        "requested",
        "configuring",
        "pre_provision",
        "provisioning",
        "pre_operational",
        "operational",
        "running",
        "pre_check",
        "pre_start",
        "pre_stop",
        "stopped",
        "pre_delete",
        "deleted"])

# TODO: remove
HostState = fsm_factory(
    "host", ["requested", "scheduling", "unknown", "up", "deleting", "down"])

MonitoredState = fsm_factory(
    "monitored", [
        "up",
        "down"])

MembershipState = fsm_factory(
    "membership", [
        "created",
        "invited",
        "accepted",
        "active",
        "expired",
        "withdrawn"
    ])


RegistrationState = fsm_factory(
    "registration", [
        "pre_registration_person",
        "pre_registration_inetorgperson",
        "pre_registration_inetorgperson_cn",
        "pre_user_inetorgperson_dn",
        "pre_user_posixaccount",
        "user_posixaccount",
        "pre_user_ldappublickey",
        "valid",
        "active",
        "expired",
        "withdrawn",
])

SubscriptionState = fsm_factory(
    "subscription", ["maintenance", "unchecked", "inactive", "active"])
