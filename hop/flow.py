from __future__ import print_function
__author__ = 'Denis Mikhalkin'

class MessageState(object):
    def __init__(self, context, msg, queue=None, path=None):
        self.context = context
        self.msg = msg
        self.path = path
        self._state = MessageState.getCurrentFlow(msg, path) 
        self.queue = queue

    def handle(self, func):
        self._state.append({'step':{'callback':func.func_name}})
        return MessageState(self.context, self.msg, self.queue, self.path)

    def schedule(self):
        self.context.publish(self.msg, self.queue)

    @staticmethod
    def getCurrentFlow(msg, path):
        if 'flow' in msg['_system']:
            root = msg['_system']['flow']
        else:
            root = []
            msg['_system']['flow'] = root

        if path is None: return root

        while len(path) != 0:
            step = path.pop(0)
            root = root[step]

        return root

    @staticmethod
    def getCurrentStep(msg, path):
        if 'flow' in msg['_system']:
            root = msg['_system']['flow']
        else:
            return None
        
        if path is None:
            if type(root) == list and len(root) > 0:
                 return root[0]['step'] if 'step' in root[0] else None
            else:
                return None
            
        if type(path) == list:
            while len(path) != 0:
                step = path.pop(0)
                root = root[step]

            return root['step'] if 'step' in root else None
            
