__author__ = 'Denis Mikhalkin'

# TODO Unit test: Filter, Join, Collect, Merge
# TODO Request count should be extracted as it differs between local and Kinesis modes
# TODO Stop signal should be extract as it differs between local and Kinesis modes
# TODO Exception handling - if error occurs, message is retried X number of times
# TODO Stop signal
# TODO Queue types
# TODO Remove priority, replace with explicit queue name
# TODO Logging
# TODO Error handling
# TODO Command line: deploy, start, stop
# TODO CollectAs - specify message type

class ContextConfig(object):
    def __init__(self, autoStop=False, autoStopLimit=0):
        self.autoStop = autoStop
        self.autoStopLimit = autoStopLimit


class Context(object):
    def __init__(self, config=None):
        self.config = config or ContextConfig()
        self.rules = dict(filter=dict(), handler=dict(), join=dict())
        self.terminated = False
        self.requestCount = 0

    def _register(self, rule, kind, callback, order=None, condition=None):
        print "Registering %s %s -> %s" % (kind, rule, callback)
        if rule not in self.rules[kind]:
            self.rules[kind][rule] = [callback]
        else:
            # TODO Implement order
            self.rules[kind][rule].append(callback)

    def _containsRule(self, rule, kind):
        return rule in self.rules[kind]

    def _checkForStop(self):
        self.requestCount += 1
        if self.terminated:
            return True
        if self.config.autoStop and self.requestCount > self.config.autoStopLimit:
            print "Stopping because of limit on requests %s" % self.config.autoStopLimit
            return True
        return False

    def _process(self, msg):
        if self._checkForStop(): return
        if msg is not None:
            if type(msg) == dict:
                if 'messageType' in msg and self._containsRule(msg['messageType'], 'handler'):
                    msg = self._filterMsg(msg)
                    if msg is not None:
                        # TODO Error handling
                        self._invokeRule(msg['messageType'], 'handler', msg)

    def _filterMsg(self, msg):
        filters = self.rules['filter']
        if msg['messageType'] in filters:
            filterCallbacks = filters[msg['messageType']]
            for callback in filterCallbacks:
                if self.terminated: return None
                # TODO Error handling
                msg = callback(msg)
                if msg is None:
                    break
        return msg

    def _invokeRule(self, rule, kind, msg):
        for callback in self.rules[kind][rule]:
            if self.terminated: return
            callback(msg)

    def webHandler(self, rule):
        # TODO Register web rule
        def caller(f):
            return f
        return caller

    def message(self, rule):
        # if self._containsRule(rule, 'handler'):
        #     raise Exception('Duplicate handler for rule ' + rule)
        def caller(f):
            self._register(rule, 'handler', f)
            return f
        return caller

    def filter(self, rule, order):
        def caller(f):
            self._register(rule, 'filter', f, order=order)
            return f
        return caller

    def join(self, condition, message=None, discard=None, minimumCount=1):
        def caller(f):
            self._register(message, 'reduce', f, condition=condition)
            return f
        return caller

    def stop(self):
        self.terminated = True

    def forget(self, msgs):
        pass

    def publish(self, msg):
        if self.terminated:
            return



