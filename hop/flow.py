from __future__ import print_function
__author__ = 'Denis Mikhalkin'

class MessageState(object):
    def __init__(self, context, msg, path=None):
        self.context = context
        self.msg = msg
        self.path = path
        self._state = MessageState._getCurrentFlow(msg, path) 

    def handle(self, func):
        self._state.append({'step':{'callback':func.func_name}})
        return MessageState(self.context, self.msg, (self.path or []).append(len(self._state)-1))

    @staticmethod
    def _getCurrentFlow(msg, path):
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
