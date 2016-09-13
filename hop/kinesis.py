import base64
import json

from hop import Context

__author__ = 'Denis Mikhalkin'

"""
AWS Kinesis source mapped into an AWS Lambda function
"""

class LambdaContext(Context):
    def __init__(self, config=None):
        super(LambdaContext, self).__init__(self, config)

    def lambda_handler(self, event, context):
        for record in event['Records']:
            payload = base64.b64decode(record['kinesis']['data'])
            try:
                self._process(json.loads(payload))
            except:
                # TODO Logging
                pass
