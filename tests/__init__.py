from hop.local import LocalContext

__author__ = 'Denis Mikhalkin'

import unittest

context = LocalContext()

class MessageTest(unittest.TestCase):

    def test_publish_receive_message_by_type(self):

        passed = [False]

        @context.message('testMessage')
        def handler(msg):
            print "Handler called with " + str(msg)
            self.assertTrue(msg is not None)
            passed[0] = True

        context.publish(dict(messageType='testMessage'))
        context.run()
        self.assertTrue(passed[0])
