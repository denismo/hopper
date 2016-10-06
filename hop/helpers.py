from __future__ import print_function
import os
import pkgutil
import sys
__author__ = 'Denis Mikhalkin'

def getRootDir():
    return os.path.join(os.path.dirname(__file__), os.path.pardir)

def getGlobalCallback(name):
    def walk_module(moduleObject):
        if hasattr(moduleObject, 'geoIPLookup'):
            return getattr(moduleObject, 'geoIPLookup')
        
        for k in dir(moduleObject):
            if type(getattr(moduleObject, k)).__name__ == "module" and getattr(moduleObject, k).__name__.startswith(moduleObject.__name__):
                res = walk_module(getattr(moduleObject, k))
                if res is not None: return res
        return None
        
    directory = [getRootDir()]
    modules = [name for _, name, _ in pkgutil.iter_modules(directory)]
    for moduleName in modules:
        print(moduleName)
        if moduleName in sys.modules:
            moduleObject = sys.modules[moduleName]
            res = walk_module(moduleObject)
            if res is not None:
                return res

    return None