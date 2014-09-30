#!/usr/bin/env python3
# encoding: UTF-8

import unittest

import cloudhands.common.states
from cloudhands.common.discovery import fsms
from cloudhands.common.discovery import providers


class DiscoveryTest(unittest.TestCase):

    def test_state_machines(self):
        self.assertIn(cloudhands.common.states.SubscriptionState, fsms)
        self.assertIn(cloudhands.common.states.HostState, fsms)
    
    def test_provider_config(self):
        configs = {cfg["metadata"]["path"]: cfg
                  for p in providers.values() for cfg in p}
        config = configs["cloudhands.jasmin.vcloud.ref-portalTest-U.cfg"]
        print(config["host"]["name"])
