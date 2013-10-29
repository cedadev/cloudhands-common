#!/usr/bin/env python3
# encoding: UTF-8

import unittest

import cloudhands.common.schema
from cloudhands.common.discovery import state_machines


class DiscoveryTest(unittest.TestCase):

    def test_state_machines(self):
        self.assertIn(cloudhands.common.schema.CredentialState,
                      state_machines())
