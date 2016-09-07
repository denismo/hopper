from heapq import heappop, heappush

__author__ = 'Denis Mikhalkin'

# http://stackoverflow.com/questions/1857780/sparse-assignment-list-in-python
class SparseList(list):
    def __setitem__(self, index, value):
        missing = index - len(self) + 1
        if missing > 0:
            self.extend([None] * missing)
        list.__setitem__(self, index, value)
    def __getitem__(self, index):
        try: return list.__getitem__(self, index)
        except IndexError: return None

class Context(object):
    def __init__(self, autoStop=False, autoStopLimit=100):
        self.rules = dict(filter=dict(), handler=dict())
        self.terminated = False
        self.queues = SparseList()
        self.autoStop = autoStop
        self.autoStopLimit = autoStopLimit
        self.requestCount = 0

    def _register(self, rule, kind, callback, order=None):
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
        if self.autoStop and self.requestCount > self.autoStopLimit:
            print "Stopping because of limit on requests %s" % self.autoStopLimit
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
                # TODO Error handling
                msg = callback(msg)
                if msg is None:
                    break
        return msg

    def _invokeRule(self, rule, kind, msg):
        self.rules[kind][rule][0](msg)

    def run(self):
        while True:
            found = False
            for index in range(len(self.queues)):
                queue = self.queues[index]
                if queue is not None and len(queue) != 0:
                    found = True
                    self._process(queue.pop(0))
                    break
            if not found:
                break

    def publish(self, msg):
        if self.terminated:
            return
        if 'priority' in msg:
            priority = msg['priority']
        else:
            priority = 1
        queue = self.queues[priority]
        if queue is None:
            queue = []
            self.queues[priority] = queue
        queue.append(msg)


    def webHandler(self, rule):
        # TODO Register web rule
        def caller(f):
            return f
        return caller

    def message(self, rule):
        if self._containsRule(rule, 'handler'):
            raise Exception('Duplicate handler for rule ' + rule)
        def caller(f):
            self._register(rule, 'handler', f)
            return f
        return caller

    def filter(self, rule, order):
        def caller(f):
            self._register(rule, 'filter', f, order=order)
            return f
        return caller

    def reduce(self, condition, message=None, discard=None, minimumCount=1):
        def caller(f):
            self._register(message, 'reduce', f, condition=condition)
            return f
        return caller


    def stop(self):
        self.terminated = True

    def forget(self, msgs, condition):
        pass



