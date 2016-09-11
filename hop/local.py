from hop import Context

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


class LocalContext(Context):
    def __init__(self, config=None):
        Context.__init__(self, config)
        self.queues = SparseList()

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

