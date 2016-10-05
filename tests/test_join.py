
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), os.path.pardir))

from hop.local import LocalContext

__author__ = 'Denis Mikhalkin'

import unittest

url = 'http://abc.com'

class JoinTest(unittest.TestCase):
    def setUp(self):
        self.context = LocalContext()
        self.stack = ''

    def geoIPLookup(msg):
        self.stack = self.stack + 'geoIPLookup,'

    def resolveUserAgent(msg):
        self.stack = self.stack + 'resolveUserAgent,'
    def enrichedPageView(msg):
        self.stack = self.stack + 'enrichedPageView,'

    def test_join_from_webhandler(self):
        # "fork" tells the handlers to run in parallel, otherwise execution is sequential
        # "then" will run after "handle" asynchronously using another Lambda invocation, taking any input "handle" produces
        # another "handle" will run in parallel with the handle-then above, processing the "pageView" message
        # join will delay the final handlers until all above paths produced results and 
        # group them by parentMessageID into one message handled by "enrichedPageView"
        self.context.publish(self.context.message(messageType='pageView', url=url)) \
            .fork() \
            .handle(geoIPLookup) \
            .handle(resolveUserAgent) \
            .join(enrichedPageView)

        self.context.run()
        self.assertEqual(self.stack, 'geoIPLookup,resolveUserAgent,enrichedPageView,')

    def test_join_from_webhandler_straight_join(self):
        # This is also possible as there could be global handlers. The join will be on parent message ID.
        self.context.publish(self.context.message(messageType='pageView', url=url)) \
            .join(enrichedPageView)

        self.context.run()
        self.assertEqual(self.stack, 'enrichedPageView,')

    def test_join_from_webhandler_sequential(self):
        # This is also possible as there could be global handlers. The join will be on parent message ID.
        self.context.publish(self.context.message(messageType='pageView', url=url)) \
            .handle(geoIPLookup) \
            .join(enrichedPageView)

        self.context.run()
        self.assertEqual(self.stack, 'geoIPLookup,enrichedPageView,')

    def test_join_from_webhandler_sequential2(self):
        # This is also possible as there could be global handlers. The join will be on parent message ID.
        self.context.publish(self.context.message(messageType='pageView', url=url)) \
            .handle(geoIPLookup) \
            .handle(resolveUserAgent) \
            .join(enrichedPageView)

        self.context.run()
        self.assertEqual(self.stack, 'geoIPLookup,resolveUserAgent,enrichedPageView,')
