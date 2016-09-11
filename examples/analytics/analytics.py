from examples.analytics import lookupUserAgent, incrementPageView, incrementUserCounter, parsePath
from hop.kinesis import LambdaContext
from hop.local import LocalContext

__author__ = 'Denis Mikhalkin'

from hop import Context, ContextConfig

# Use case: web analytics (page views, unique users, geo ip lookup (block), user lookup(block), user agent lookup(block))

if __name__ == '__main__':
    context = LocalContext(ContextConfig(autoStop=True, autoStopLimit=100))
else:
    # By default, make sure the sample stops on Lambdato avoid incurring costs
    context = LambdaContext(ContextConfig(autoStop=True, autoStopLimit=100))

@context.webHandler("webRequest")
@context.message('pageView')
def pageView(msg):
    url = msg['url']
    context.publish(dict(messageType='internalPageView', url=url))\
        .collect('enrichedPageView') \
        .mergeAs('enrichedFinalPageView')

@context.message('internalPageView')
def geoIPLookup(msg):
    # Lookup IP
    url = msg['url']
    country=''
    context.publish(msg.update(dict(messageType='enrichedPageView', country='')))

# Note that it matches the original message
@context.message('enrichedFinalPageView')
def uniqueUsers(msg):
    cookie = msg['cookie']
    country = msg['country']
    # Increment user counter recording their country
    incrementUserCounter(cookie, country)
    # Nothing published

@context.message('enrichedFinalPageView')
def enrichedPageView(msg):
    country = msg['country']
    url = msg['url']
    path = parsePath(url)
    # Increment page views recording device country
    incrementPageView(path, country)
    # Nothing published

@context.message('internalPageView')
def resolveUserAgent(msg):
    userAgent = msg['userAgent']
    browserInfo = lookupUserAgent(userAgent)
    context.publish(msg.update(dict(messageType='enrichedPageView').update(browserInfo)))

# Alternative to .collect - collect all message which have the same parentMessageID
# This method will receive original 'enrichedPageView' messages, first each one of them, and eventually all of them
@context.reduce(message='enrichedPageView', condition='parentMessageID', discard='5s')
def collectPageViews(msgs):
    if not msgs.checkFieldsInMessages('country', 'deviceType'):
        return

    context.forget(msgs)
    country = msgs['country']
    url = msgs['url']
    path = parsePath(url)
    # Increment page views recording device country
    incrementPageView(path, country)

# Default handler for Lambda implementation
def lambda_handler(event, lambda_context):
    context.lambda_handler(event, lambda_context)

if __name__ == '__main__':
    # Using default implementation for testing
    context.publish(dict(messageType='pageView', url='http://abc.com', cookie='abc', userAgent='Chrome'))
    context.run()