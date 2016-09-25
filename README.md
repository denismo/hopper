Hopper
======

Hopper is a framework that allows writing message-driven distributed applications in Python, deployed on AWS Lambda.
It removes the boilerplate code associated with message passing, queueing, matching and so on, letting you focus on the business logic of message handlers.
It is inspired by [Akka actors](http://doc.akka.io/docs/akka/snapshot/intro/what-is-akka.html), [AWSLabs Chalice](https://github.com/awslabs/chalice), and [GigaSpaces](http://www.gigaspaces.com/).

Usage scenarios
===============
- A web crawler
- Analytics
- Distributed realtime processing graphs (the ones you'd write in [Apache Storm](http://storm.apache.org/))

Design
======

The key input into the framework is a message handler, associated with a certain message type. 
The framework ensures that when the message of such type is received, it is dispatched to the handler.

It does that by managing message queue (currently Kinesis), and providing primitives for declaring handlers and firing messages.
Eventually, it is also meant to work together with something like Chalice or Serverless, receiving messages initially via Web API (and any other sources), 
and then injecting them into message queue.

All processing is happening on AWS Lambda so there are no servers, and all processing is asynchronous. 
The framework uses Kinesis (queue) and DynamoDB (status, statistics, some state). 


Features
=======

|API|Description|
|---|-----------|
|@context.message|Marks a message handler for a message of certain type|
|@context.filter|Marks a message filter for a message of certain type|
|context.publish|Sends a message for processing by the framework (asynchronously)|

Examples
============

Message type handler
--------------------

- the pageUrl handler receives `pageUrl` messages, does quick processing (such as downloading the page body), and fires the body message
- the pageBody handler receives `pageBody` messages, parses the body, and fires `pageUrl` message for each found URL  

```python
@context.message("pageUrl")
def pageUrl(msg):
    if 'url' in msg and msg['url'] is not None:
        if not isUrlProcessed(msg['url']):
            body = download(msg['url'])
            markUrlProcessed(msg['url'])
            if body is not None:
                context.publish(dict(messageType='pageBody', body=body))


@context.message('pageBody')
def pageBody(msg): # 
    if 'body' in msg and msg['body'] is not None:
        urls = extractUrls(msg['body'])
        for url in urls:
            if not isUrlProcessed(url):
                context.publish(dict(messageType='pageUrl', url=url, priority=(0 if url.startswith('https') else 1)))
```

Filter (executed before handlers)
-------

This ia a simple filter that stops processing of `pageURL` messages containing certain URLs by returning None. 

```python
@context.filter('pageUrl', 1)
def urlFilter(msg):
    if 'url' in msg and msg['url'] is not None and not msg['url'].find('au-mg6') != -1:
        return msg
    else:
        return None
```

Future direction
================

The current implementation is just a proof of concept. I can envision a lot of features before it is really useful:

- Fork/Join
- Map/Reduce
- Apache Spark-style fluent API (see analytics.py/pageView for example)
- Multiple queues for managing priority
- Different sources (SQS, S3, API Gateway, DynamoDB)
- Retries
- Correlation
- Throttling
- Read-receipts

Some of these are typical of queue-based processing, but not necessarily applicable:
- Rollback actions
- Transactions
- Ordering

Installation
============

Requires:

    - Python 2.7
    - Boto 3
    - Python-lambda 0.4+ (deployment only)


1. Create a virtual environment
1. Install dependencies into it:

        pip install -r requirements.txt

1. Activate virtual environment
1. Set AWS profile of the deployment user (below)
1. Deploy the demo crawler applications

        python hop/run.py deploy

1. Go into AWS Lambda console, locate the `hopper` function and add test input

        {
            "messageType":"pageUrl",
            "url":"http://abc.com"
        }

1. Run "Test" for the AWS Lambda function
1. Check the CloudWatch logs for the output.
 
    You should see a number of `pageUrl` entries, without any errors.


Security Configuration
======================

In order to run the examples (and your own code), you'll need to create two security entities:
- AWS Lambda execution role (required)
- Deployment user (only if you want to deploy automatically)

AWS Lambda execution role needs the following permissions (assuming the DynamoDB table "HopperRuntime", the Kinesis stream "HopperQueue", and the function name "hopper"):

        {
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "dynamodb:BatchGetItem",
                        "dynamodb:BatchWriteItem",
                        "dynamodb:DeleteItem",
                        "dynamodb:DescribeTable",
                        "dynamodb:GetItem",
                        "dynamodb:GetRecords",
                        "dynamodb:ListTables",
                        "dynamodb:PutItem",
                        "dynamodb:Query",
                        "dynamodb:Scan",
                        "dynamodb:UpdateItem"
                    ],
                    "Resource": [
                        "arn:aws:dynamodb:ap-southeast-2:1234567890:table/HopperRuntime"
                    ]
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "kinesis:DescribeStream",
                        "kinesis:GetShardIterator",
                        "kinesis:GetRecords",
                        "kinesis:ListStreams",
                        "kinesis:PutRecord",
                        "kinesis:PutRecords"
                    ],
                    "Resource": [
                        "arn:aws:kinesis:ap-southeast-2:1234567890:stream/HopperQueue"
                    ]
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:PutLogEvents"
                    ],
                    "Resource": "*"
                },
                {
                    "Effect": "Allow",
                    "Action": "lambda:InvokeFunction",
                    "Resource": "arn:aws:lambda:ap-southeast-2:1234567890:function:hopper"
                },
                {
                    "Effect": "Allow",
                    "Action": "kinesis:ListStreams",
                    "Resource": "arn:aws:kinesis:ap-southeast-2:1234567890:stream/*"
                }
            ]
        }

The deployment user need the following permissions:

        {
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "lambda:GetEventSourceMapping"
                    ],
                    "Resource": [
                        "arn:aws:lambda:ap-southeast-2:1234567890:event-source-mappings:*"
                    ]
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "lambda:ListEventSourceMappings",
                        "iam:GetUser",
                        "lambda:UpdateEventSourceMapping",
                        "lambda:CreateEventSourceMapping",
                        "lambda:CreateFunction",
                        "dynamodb:ListTables",
                        "kinesis:ListStreams",
                        "lambda:ListFunctions"
                    ],
                    "Resource": [
                        "*"
                    ]
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "lambda:UpdateFunction",
                        "lambda:UpdateFunctionCode",
                        "lambda:UpdateFunctionConfiguration"
                    ],
                    "Resource": "arn:aws:lambda:ap-southeast-2:1234567890:function:hopper"
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "iam:PassRole"
                    ],
                    "Resource": "arn:aws:iam::1234567890:role/hopper-runtime"
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "dynamodb:DescribeTable",
                        "dynamodb:GetItem",
                        "dynamodb:PutItem",
                        "dynamodb:UpdateItem",
                        "dynamodb:DeleteItem"
                    ],
                    "Resource": [
                        "arn:aws:dynamodb:ap-southeast-2:1234567890:table/HopperRuntime"
                    ]
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "kinesis:DescribeStream"
                    ],
                    "Resource": [
                        "arn:aws:kinesis:ap-southeast-2:1234567890:stream/HopperQueue"
                    ]
                }
            ]
        }

License
=======
[Apache License 2.0](LICENSE)
