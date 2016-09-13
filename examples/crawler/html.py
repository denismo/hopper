import re

__author__ = 'Denis Mikhalkin'

urlRe = re.compile('(?:https?://)?[\da-z.-]+\.[a-z.]{2,6}[/\w .-]*/?')

def extractUrls(body):
    matches = urlRe.findall(body)
    return matches