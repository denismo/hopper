from __future__ import print_function
from examples.crawler.db import isUrlProcessed, markUrlProcessed
from hop import Context, ContextConfig
from hop.local import LocalContext
from hop.kinesis import LambdaContext
from examples.crawler.html import extractUrls
from examples.crawler.webio import download

__author__ = 'Denis Mikhalkin'

import logging
logger = logging.getLogger("hopper.crawler")

if __name__ == '__main__':
    context = LocalContext(ContextConfig(autoStop=True, autoStopLimit=100))
    logging.basicConfig(format='%(levelname)s | %(filename)s | %(message)s', level=logging.DEBUG)
else:
    # By default, make sure the sample stops on Lambdato avoid incurring costs
    context = LambdaContext(ContextConfig(autoStop=True, autoStopLimit=100, dynamoDBRegion='ap-southeast-2', kinesisRegion='ap-southeast-2'))

@context.webHandler("webRequest")
@context.handle("pageUrl")
def pageUrl(msg):
    logger.info("pageUrl %s" % msg)
    if 'url' in msg and msg['url'] is not None:
        # TODO Check if URL has been processed
        if not isUrlProcessed(msg['url']):
            body = download(msg['url'])
            markUrlProcessed(msg['url'])
            if body is not None:
                context.publish(context.message(messageType='pageBody', body=body))
            else:
                logger.debug('Body is None')
        else:
            logger.debug('URL has been processed')
    else:
        logger.warn('url is None in pageUrl(msg)')

@context.handle('pageBody')
def pageBody(msg): # TODO Unwrap parameters
    logger.info("pageBody %s" % msg)
    if 'body' in msg and msg['body'] is not None:
        urls = extractUrls(msg['body'])
        for url in urls:
            if not isUrlProcessed(url):
                context.publish(context.message(messageType='pageUrl', url=url, priority=(0 if url.startswith('https') else 1)))
    else:
        logger.warn('body is None in pageBody(msg)')

@context.filter('pageUrl', 1)
def urlFilter(msg):
    if 'url' in msg and msg['url'] is not None and not msg['url'].find('au-mg6') != -1:
        return msg
    else:
        return None

@context.filter('pageUrl', 0)
def nopFilter(msg):
    return msg

# Default handler for Lambda implementation
def lambda_handler(event, lambda_context):
    context.lambda_handler(event, lambda_context)

if __name__ == '__main__':
    logger.info('Running crawler')
    context.publish(context.message(messageType='pageUrl', url='http://abc.com'))
    context.run()
