__author__ = 'Denis Mikhalkin'

_processed = dict()

def isUrlProcessed(url):
    return url in _processed

def markUrlProcessed(url):
    _processed[url] = url