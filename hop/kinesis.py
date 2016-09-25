import base64
import json
import boto3
import uuid

from hop import Context
import logging
logger = logging.getLogger("hopper.kinesis")
logger.setLevel(logging.INFO)

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
        self.table.update_item(
            Key={
                'Object': 'RuntimeState',
            },
            AttributeUpdates={
                'RequestCounter': {'Action': 'ADD',
                'Value': 1}                
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
            item = response['Item'] if 'Item' in response else None
            return item['RequestCounter'] if item is not None and 'RequestCounter' in item else 0

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
            item = response['Item'] if 'Item' in response else None
            return item['Terminated'] if item is not None and 'Terminated' in item else False

    def lambda_handler(self, event, context):
        logger.info("Lambda handler got called with %s%s", type(event), json.dumps(event))
        if event is not None and 'Records' in event:
            for record in event['Records']:
                payload = base64.b64decode(record['kinesis']['data'])
                try:
                    self._process(json.loads(payload))
                except:
                    logger.exception("Unable to process message " + str(payload))
                    pass
        else:
            try:
                if type(event) == str:
                    self._process(json.loads(event))
                elif type(event) == dict:
                    self._process(event)
                else:
                    logger.error("Unexpected type of message: %s" % type(event))
            except:
                logger.exception("Unable to process message " + str(event))
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