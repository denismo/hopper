
import sys
sys.path.append('e:\\WS\\Hopper')

from hop.local import LocalContext

__author__ = 'Denis Mikhalkin'

import unittest

class ContextTest(unittest.TestCase):

    def setUp(self):
        self.context = LocalContext()

    def test_publish_receive_message_by_type(self):

        passed = [False]

        @self.context.handle('testMessage')
        def handler(msg):
            self.assertTrue(msg is not None)
            passed[0] = True

        self.context.publish(self.context.message(messageType='testMessage'))
        self.context.run()
        self.assertTrue(passed[0])

    def test_publish_does_not_receive_message_by_wrong_type(self):

        passed = [False]

        @self.context.handle('testMessage2')
        def handler(msg):
            self.assertTrue(msg is not None)
            passed[0] = True

        self.context.publish(self.context.message(messageType='testMessage'))
        self.context.run()
        self.assertFalse(passed[0])

    def test_publish_does_not_receive_message_after_stop(self):

        passed = [True]

        @self.context.handle('testMessage')
        def handler(msg):
            self.assertTrue(msg is not None)
            self.context.stop()

        @self.context.handle('testMessageAfter')
        def handler(msg):
            self.assertTrue(msg is not None)
            passed[0] = False

        self.context.publish(self.context.message(messageType='testMessage'))
        self.context.publish(self.context.message(messageType='testMessageAfter'))
        self.context.run()
        self.assertTrue(passed[0])
    
    def test_filter(self):
        passed = [False]

        @self.context.filter('testMessage')
        def handler(msg):
            self.assertTrue(msg is not None)
            passed[0] = True
            return msg 

        self.context.publish(self.context.message(messageType='testMessage'))
        self.context.run()
        self.assertTrue(passed[0])
                   

if __name__ == '__main__':
    unittest.main()