
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), os.path.pardir))

from hop.local import LocalContext
from hop.flow import MessageState
import json

__author__ = 'Denis Mikhalkin'

import unittest

class MessageStateTest(unittest.TestCase):

    def setUp(self):
        self.context = LocalContext()
        self.msg = self.context.message('pageUrl')

    def test_create(self):
        MessageState(self.context, self.msg)
        print(self.msg)

    def test_handle(self):
        state = MessageState(self.context, self.msg).handle(self.test_handle)
        print(self.msg)

    def test_handle_handle(self):
        state = MessageState(self.context, self.msg).handle(self.test_handle).handle(self.test_handle_handle)
        print(self.msg)
