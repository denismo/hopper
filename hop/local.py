from hop import Context, ContextSPI

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

class LocalContextSPI(ContextSPI):
    def __init__(self, config=None):
        ContextSPI.__init__(self, config)
        self.queues = SparseList()
        self.requestCount = 0
        self.terminated = False
    
    def _incrementRequestCount(self):
        self.requestCount += 1

    def _getRequestCount(self):
        return self.requestCount

    def _getTerminated(self):
        return self.terminated

    def stop(self):
        self.terminated = True

    def publish(self, msg, queueName=None):
        if self.terminated:
            return
        if 'priority' in msg:
            priority = msg['priority']
        else:
            priority = self._queueIndex(queueName) if queueName is not None else 1
        queue = self.queues[priority]
        if queue is None:
            queue = []
            self.queues[priority] = queue
        queue.append(msg)

    def _queueIndex(self, queueName):
        if 'queues' in self.config:
            queues = self.config['queues']
            index = 0
            for key in queues:
                if key == queueName:
                    return index
                index += 1

        return 1        

class LocalContext(Context):
    def __init__(self, config=None):
        Context.__init__(self, config, LocalContextSPI)

    def run(self):
        while not self._getTerminated():
            found = False
            for index in range(len(self.spi.queues)):
                if self._getTerminated(): return
                queue = self.spi.queues[index]
                if queue is not None and len(queue) != 0:
                    found = True
                    self._process(queue.pop(0))
                    break
            if not found:
                break

