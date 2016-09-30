
import sys
sys.path.append('e:\\WS\\Hopper')

from hop.local import LocalContext

__author__ = 'Denis Mikhalkin'

import unittest

class MessageTest(unittest.TestCase):
    def setUp(self):
        self.context = LocalContext()

    def test_empty_messageType(self):
        try:
            msg = self.context.message(messageType='')
            msg = self.context.message(messageType=None)
            self.fail('Did not validate messageType')
        except:
            pass

    def test_default(self):
        msg = self.context.message(messageType='abc')
        self.assertEqual(msg['messageType'], 'abc')
        self.assertIsNotNone(msg['_system'])
        self.assertIsNotNone(msg['_system']['messageID'])
        self.assertIsNotNone(msg['_system']['timestamp'])

