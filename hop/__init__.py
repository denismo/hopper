from __future__ import print_function
__author__ = 'Denis Mikhalkin'

import uuid
import logging
from datetime import datetime
logger = logging.getLogger("hopper.base")
logger.setLevel(logging.INFO)

# TODO Message ID, parent/child
# TODO Doc Comments and comments in code
# TODO Unit test: Filter, Join, Collect, Merge
# TODO Exception handling - if error occurs, message is retried X number of times
# TODO Queue types
# TODO Remove priority, replace with explicit queue name
# TODO Logging
# TODO Error handling
# TODO Command line: start, stop
# TODO CollectAs - specify message type
# TODO Example use cases: https://github.com/claudiajs/example-projects
# TODO Check https://github.com/nficano/python-lambda source code, for potential simplified deployment
# TODO Another uploader: https://github.com/rackerlabs/lambda-uploader
# TODO Another installer: https://github.com/garnaat/kappa
# TODO Another installer https://github.com/awslabs/chalice

class ContextConfig(object):
    def __init__(self, autoStop=False, autoStopLimit=0, dynamoDBRegion='', kinesisRegion=''):
        self.autoStop = autoStop
        self.autoStopLimit = autoStopLimit
        self.dynamoDBRegion = dynamoDBRegion
        self.kinesisRegion = kinesisRegion

class Message(dict):
    def __init__(self, messageType, params):
        if messageType is None or messageType == '':
            raise Exception('messageType must be non-empty string')
        if params is not None:
            self.update(params)
        self['messageType'] = messageType
        self['_system'] = {
            'messageID': uuid.uuid4(),
            'timestamp': datetime.utcnow()
        }

class Context(object):
    def __init__(self, config=None):
        self.config = config or ContextConfig()
        self.rules = dict(filter=dict(), handler=dict(), join=dict())

    ######### Internals ################

    def _register(self, rule, kind, callback, order=None, condition=None):
        logger.info("Registering %s %s -> %s", kind, rule, callback)
        if rule not in self.rules[kind]:
            self.rules[kind][rule] = [callback]
        else:
            # TODO Implement order
            self.rules[kind][rule].append(callback)

    def _containsRule(self, rule, kind):
        return rule in self.rules[kind]

    def _checkForStop(self):
        if self._getTerminated():
            return True
        if self.config.autoStop and self._getRequestCount() > self.config.autoStopLimit:
            logger.info("Stopping because of limit on requests %s", self.config.autoStopLimit)
            return True
        return False

    def _process(self, msg):
        self._incrementRequestCount()
        if self._checkForStop(): return
        if msg is not None:
            if (type(msg) == dict or type(msg) == Message) and 'messageType' in msg:
                msg = self._filterMsg(msg)
                if msg is not None:
                    if self._containsRule(msg['messageType'], 'handler'):
                        # TODO Error handling
                        self._invokeRule(msg['messageType'], 'handler', msg)

    def _filterMsg(self, msg):
        filters = self.rules['filter']
        if msg['messageType'] in filters:
            filterCallbacks = filters[msg['messageType']]
            for callback in filterCallbacks:
                if self._getTerminated(): return None
                # TODO Error handling
                msg = callback(msg)
                if msg is None:
                    break
        return msg

    def _invokeRule(self, rule, kind, msg):
        # TODO Problem: the handlers for the same message type are supposed to be running in parallel, not sequentially
        for callback in self.rules[kind][rule]:
            if self._getTerminated(): return
            callback(msg)

    ######### Overides #########

    def _getTerminated(self):
        raise NotImplemented("_getTerminated is not implemented by default")

    def _getRequestCount(self):
        raise NotImplemented("_getRequestCount is not implemented by default")

    def _incrementRequestCount(self):
        raise NotImplemented("_incrementRequestCount is not implemented by default")

    ######### Wrappers #############

    def webHandler(self, rule):
        # TODO Register web rule
        def caller(f):
            return f
        return caller

    def handle(self, rule):
        def caller(f):
            self._register(rule, 'handler', f)
            return f
        return caller

    def filter(self, rule, order=None):
        def caller(f):
            self._register(rule, 'filter', f, order=order)
            return f
        return caller

    def join(self, condition, message=None, discard=None, minimumCount=1):
        def caller(f):
            self._register(message, 'reduce', f, condition=condition)
            return f
        return caller


    ########### Actions #############

    def message(self, messageType, **kwargs):
        return Message(messageType, kwargs)

    def stop(self):
        pass

    def forget(self, msgs):
        pass

    def publish(self, msg):
        if self.terminated:
            return



