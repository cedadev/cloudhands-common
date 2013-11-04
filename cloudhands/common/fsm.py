#!/usr/bin/env python3
# encoding: UTF-8

from cloudhands.common.schema import fsm_factory

CredentialState = fsm_factory(
    "credential", ["untrusted", "trusted", "expired"])

ResourceState = fsm_factory(
    "resource", ["unknown", "up", "down"])
