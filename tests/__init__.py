from hop.local import LocalContext

__author__ = 'Denis Mikhalkin'

import unittest

class MessageTest(unittest.TestCase):

    def setUp(self):
        self.context = LocalContext()

    def test_publish_receive_message_by_type(self):

        passed = [False]

        @self.context.message('testMessage')
        def handler(msg):
            self.assertTrue(msg is not None)
            passed[0] = True

        self.context.publish(dict(messageType='testMessage'))
        self.context.run()
        self.assertTrue(passed[0])

    def test_publish_does_not_receive_message_by_wrong_type(self):

        passed = [False]

        @self.context.message('testMessage2')
        def handler(msg):
            self.assertTrue(msg is not None)
            passed[0] = True

        self.context.publish(dict(messageType='testMessage'))
        self.context.run()
        self.assertFalse(passed[0])

    def test_publish_does_not_receive_message_after_stop(self):

        passed = [True]

        @self.context.message('testMessage')
        def handler(msg):
            self.assertTrue(msg is not None)
            self.context.stop()

        @self.context.message('testMessageAfter')
        def handler(msg):
            self.assertTrue(msg is not None)
            passed[0] = False

        self.context.publish(dict(messageType='testMessage'))
        self.context.publish(dict(messageType='testMessageAfter'))
        self.context.run()
        self.assertTrue(passed[0])



