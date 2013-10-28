#!/usr/bin/env python3
#   encoding: UTF-8

import unittest


from cloudhands.common.schema import CredentialState

class TestCredentialState(unittest.TestCase):

    def test_initialisation(self):
        obj = CredentialState.init()
        self.assertEqual(CredentialState.table, obj.fsm)
        self.assertEqual(CredentialState.values[0], obj.name)
        print(vars(obj))

if __name__ == "__main__":
    unittest.main()
