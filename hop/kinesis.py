import base64
import json
import boto3
import uuid

from hop import Context
import logging
logger = logging.getLogger()

__author__ = 'Denis Mikhalkin'

"""
AWS Kinesis source mapped into an AWS Lambda function
"""

class LambdaContext(Context):
    def __init__(self, config=None):
        Context.__init__(self, config)
        logger.info("Lambda context started")        
        dynamodb = boto3.resource('dynamodb')
        self.kinesisClient = boto3.client('kinesis')
        self.table = dynamodb.Table('HopperRuntime')

    def _incrementRequestCount(self):
        table.update_item(
            Key={
                'Object': 'RuntimeState',
            },
            UpdateExpression="set RequestCounter = RequestCounter + :val",
            ExpressionAttributeValues={
                ':val': 1
            }
        )        

    def _getRequestCount(self):
        try:
            response = self.table.get_item(
                Key={
                    'Object': 'RuntimeState',
                }
            )
        except ClientError as e:
            print(e.response['Error']['Message'])
            return 0
        else:
            item = response['Item']
            return item['RequestCounter']

    def _getTerminated(self):
        try:
            response = self.table.get_item(
                Key={
                    'Object': 'RuntimeState',
                }
            )
        except ClientError as e:
            print(e.response['Error']['Message'])
            return 0
        else:
            item = response['Item']
            return item['Terminated']

    def lambda_handler(self, event, context):
        logging.info("Lambda handler got called")
        for record in event['Records']:
            payload = base64.b64decode(record['kinesis']['data'])
            try:
                self._process(json.loads(payload))
            except:
                logger.exception("Unable to process message " + str(payload))
                pass

    def stop(self):
        logger.info("Stopping the hopper")
        self.table.update_item(
            Key={
                'Object': 'RuntimeState',
            },
            UpdateExpression="set Terminated = :r",
            ExpressionAttributeValues={
                ':r': True,
            }
        )

    def publish(self, msg):
        self.kinesisClient.put_record(    
            StreamName='HopperQueue',
            Data=json.dumps(msg),
            PartitionKey=uuid.uuid4().get_hex())