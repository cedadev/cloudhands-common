#!/usr/bin/env python3
# encoding: UTF-8

import unittest

import cloudhands.common.fsm
from cloudhands.common.discovery import fsms


class DiscoveryTest(unittest.TestCase):

    def test_state_machines(self):
        self.assertIn(cloudhands.common.fsm.CredentialState, fsms)
        self.assertIn(cloudhands.common.fsm.HostState, fsms)
