from __future__ import print_function

import sys
import os
import pkgutil
sys.path.append(os.path.join(os.path.dirname(__file__), os.path.pardir))

from hop.local import LocalContext

__author__ = 'Denis Mikhalkin'

import unittest
import logging
logging.basicConfig(format='%(levelname)s | %(filename)s | %(message)s', level=logging.DEBUG)

url = 'http://abc.com'

stack = ''
def geoIPLookup(msg):
    global stack
    stack = stack + 'geoIPLookup,'
def resolveUserAgent(msg):
    global stack
    stack = stack + 'resolveUserAgent,'
def enrichedPageView(msg):
    global stack
    stack = stack + 'enrichedPageView,'


class JoinTest(unittest.TestCase):
    def setUp(self):
        global stack
        self.context = LocalContext()
        stack = ''

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
            .join(enrichedPageView) \
            .schedule()

        self.context.run()
        global stack
        self.assertEqual(stack, 'geoIPLookup,resolveUserAgent,enrichedPageView,')

    def test_join_from_webhandler_straight_join(self):
        # This is also possible as there could be global handlers. The join will be on parent message ID.
        self.context.publish(self.context.message(messageType='pageView', url=url)) \
            .join(enrichedPageView) \
            .schedule()

        self.context.run()
        global stack
        self.assertEqual(stack, 'enrichedPageView,')

    def test_join_from_webhandler_sequential(self):
        # This is also possible as there could be global handlers. The join will be on parent message ID.
        self.context.publish(self.context.message(messageType='pageView', url=url)) \
            .handle(geoIPLookup) \
            .join(enrichedPageView) \
            .schedule()

        self.context.run()
        global stack
        self.assertEqual(stack, 'geoIPLookup,enrichedPageView,')

    def test_join_from_webhandler_sequential2(self):
        # This is also possible as there could be global handlers. The join will be on parent message ID.
        self.context.publish(self.context.message(messageType='pageView', url=url)) \
            .handle(geoIPLookup) \
            .handle(resolveUserAgent) \
            .join(enrichedPageView) \
            .schedule()

        self.context.run()
        global stack
        self.assertEqual(stack, 'geoIPLookup,resolveUserAgent,enrichedPageView,')

    def test_flow_from_webhandler_no_join(self):
        # This is also possible as there could be global handlers. The join will be on parent message ID.
        self.context.flow(self.context.message(messageType='pageView', url=url)) \
            .handle(geoIPLookup) \
            .schedule()

        self.context.run()
        global stack
        self.assertEqual(stack, 'geoIPLookup,')

    def test_modules(self):
        def walk_module(moduleObject):
            if hasattr(moduleObject, 'geoIPLookup'):
                self.assertTrue(type(getattr(moduleObject, 'geoIPLookup')).__name__ == 'function')
                return True
            
            for k in dir(moduleObject):
                # print(getattr(moduleObject, k))
                if type(getattr(moduleObject, k)).__name__ == "module" and getattr(moduleObject, k).__name__.startswith(moduleObject.__name__):
                    res = walk_module(getattr(moduleObject, k))
                    if res: return True
            return False
            
        directory = ['E:/WS/Hopper']
        modules = [name for _, name, _ in pkgutil.iter_modules(directory)]
        found = False
        for moduleName in modules:
            if moduleName in sys.modules:
                moduleObject = sys.modules[moduleName]
                res = walk_module(moduleObject)
                if res:
                    found = True
                    break
        self.assertTrue(found)

if __name__ == '__main__':
    unittest.main()