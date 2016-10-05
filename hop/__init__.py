from __future__ import print_function
__author__ = 'Denis Mikhalkin'

import uuid
import logging
from datetime import datetime
import yaml
import collections
logger = logging.getLogger("hopper.base")

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

# TODO Config is too specific to the implementation. Should have generic sections, which will be interpreted by corresponding service
class ContextConfig(dict):
    def __init__(self, yamlObject=None):
        dict.__init__(self)
        if yamlObject is not None:
            self.update(yamlObject)
            for key, value in ContextConfig._traverse(yamlObject):
                self[key] = value

    def __getitem__(self, key):
        try:
            return dict.__getitem__(self, key)
        except:
            return None

    @staticmethod
    def _traverse(nested):
        for key, value in nested.iteritems():
            if isinstance(value, collections.Mapping):
                for inner_key, inner_value in ContextConfig._traverse(value):
                    yield key + '.' + inner_key, inner_value
            else:
                yield key, value        

    @staticmethod
    def fromYaml(configFile):
        with open(configFile, 'r') as stream:
            return ContextConfig(yamlObject=yaml.load(stream))


class Message(dict):
    def __init__(self, messageType, params):
        dict.__init__(self)
        if messageType is None or messageType == '':
            raise Exception('messageType must be non-empty string')
        if params is not None:
            self.update(params)
        self['messageType'] = messageType
        self['_system'] = {
            'messageID': str(uuid.uuid4()),
            'timestamp': str(datetime.utcnow())
        }

    def clone(self):
        return Message(self['messageType'], self)

class ContextSPI(object):
    def __init__(self, config=None):
        self.config = config or ContextConfig()
    
    def _getTerminated(self):
        raise NotImplemented("_getTerminated is not implemented by default")

    def _getRequestCount(self):
        raise NotImplemented("_getRequestCount is not implemented by default")

    def _incrementRequestCount(self):
        raise NotImplemented("_incrementRequestCount is not implemented by default")

    def stop(self):
        raise NotImplemented("stop is not implemented by default")

    def forget(self, msgs):
        raise NotImplemented("forget is not implemented by default")

    def publish(self, msg, queue=None):
        raise NotImplemented("publish is not implemented by default")

class Context(object):
    def __init__(self, config=None, spiClass=ContextSPI):
        self.config = config or ContextConfig()
        self.rules = dict(filter=dict(), handler=dict(), join=dict())
        self.spi = spiClass(config)

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
        if self.config['runtime.autoStop'] and self._getRequestCount() > self.config['runtime.autoStopLimit']:
            logger.info("Stopping because of limit on requests %s", self.config['runtime.autoStopLimit'])
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
        if self._getTerminated(): return

        callbacks = self.rules[kind][rule]
        if callbacks is None or len(callbacks) == 0:
            return

        callbacks = self._callbacksForMessage(callbacks, msg)

        callback = callbacks[0]
        try:
            callback(msg)
        except:
            logger.exception('Exception calling callback %s', callback)
        
        for callback in callbacks[1:]:
            newMsg = self._callbackWrappedMessage(msg, callback)
            logger.debug('Publishing parallel message: %s', newMsg)
            self.publish(newMsg, 'priority')

    def _callbacksForMessage(self, callbacks, msg):
        if 'flow' in msg['_system'] and 'currentState' in msg['_system']['flow'] and 'callback' in msg['_system']['flow']['currentState']:
            for callback in callbacks:
                if callback.func_name == msg['_system']['flow']['currentState']['callback']:
                    return [callback]
            return []
        else:
            return callbacks

    def _callbackWrappedMessage(self, msg, callback):
        """
        Creates a message with the flow state which will match the corresponding callback
        """
        callbackMsg = msg.clone()
        if 'flow' in callbackMsg['_system']:
            flow = callbackMsg['_system']['flow']
        else:
            flow = {}
        flow['currentState'] = {
            'callback': callback.func_name
        }
        callbackMsg['_system']['flow'] = flow
        return callbackMsg

    ######### Overides #########

    def _getTerminated(self):
        return self.spi._getTerminated()

    def _getRequestCount(self):
        return self.spi._getRequestCount()

    def _incrementRequestCount(self):
        return self.spi._incrementRequestCount()

    ######### Wrappers #############

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
            self._register(message, 'join', f, condition=condition)
            return f
        return caller


    ########### Actions #############

    def message(self, messageType, **kwargs):
        return Message(messageType, kwargs)

    def messageFromJson(self, messageJson):
        if type(messageJson) == str:
            loaded = json.loads(messageJson)
        else:
            loaded = messageJson
        return Message(loaded['messageType'], loaded)

    def stop(self):
        return self.spi.stop()

    def forget(self, msgs):
        return self.spi.forget()

    def publish(self, msg, queue=None):
        return self.spi.publish(msg, queue)


