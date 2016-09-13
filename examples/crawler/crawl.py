from db import isUrlProcessed, markUrlProcessed
from hop import Context
from html import extractUrls
from webio import download

__author__ = 'Denis Mikhalkin'

context = Context()

@context.webHandler("webRequest")
@context.message("pageUrl")
def pageUrl(msg):
    print "pageUrl %s" % msg
    if msg['url'] is not None:
        # TODO Check if URL has been processed
        if not isUrlProcessed(msg['url']):
            body = download(msg['url'])
            markUrlProcessed(msg['url'])
            if body is not None:
                context.publish(dict(messageType='pageBody', body=body))

@context.message('pageBody')
def pageBody(msg): # TODO Unwrap parameters
    print "pageBody %s" % msg
    if msg['body'] is not None:
        urls = extractUrls(msg['body'])
        for url in urls:
            if not isUrlProcessed(url):
                context.publish(dict(messageType='pageUrl', url=url, priority=(0 if url.startswith('https') else 1)))

@context.filter('pageUrl', 1)
def urlFilter(msg):
    if msg['url'] is not None and not msg['url'].find('au-mg6') != -1:
        return msg
    else:
        return None

@context.filter('pageUrl', 0)
def nopFilter(msg):
    return msg

if __name__ == '__main__':
    context.publish(dict(messageType='pageUrl', url='http://abc.com'))
    context.run()