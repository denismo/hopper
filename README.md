Hopper
======

Hopper is a library that allows writing message-driven distributed applications in Python, deployed on AWS Lambda.
It removes the boilerplate code associated with message passing, queueing, matching and so on, letting you focus on the business logic of message handlers.
It inspired by [Akka actors](http://doc.akka.io/docs/akka/snapshot/intro/what-is-akka.html, [Chalice](https://github.com/awslabs/chalice), and [GigaSpaces](http://www.gigaspaces.com/).

Usage scenarios
===============
- A web crawler
- Analytics
- Distributed realtime processing graphs (the ones you'd write in [Apache Storm](http://storm.apache.org/)

Design
======

The key input into the library is a message handler, associated with a certain message type. 
The library ensures that when the message of such type is received, it is dispatched to the handler.

It does that by managing message queue (currently Kinesis), and providing primitives for declaring handlers and firing messages.
Eventually, it is also meant to work together with something like Chaline or Serveless, receiving messages initially via Web API, 
and then injecting them into message queue. 

All processing is happening on AWS Lambda so there are no servers. The library uses Kinesis (queue) and DynamoDB (status, statistics, some state). 

Installation
============

Requires:
- Python 2.7
- Boto 3
- Python-lambda 0.4+ (deployment only)

1. Create a virtual environment
2. Install dependencies into it:

    pip install -r requirements.txt

3. Activate virtual environment
4. Set AWS profile of the deployment user (below)
5. Deploy the demo crawler applications

    python hop/run.py deploy

6. Go into AWS Lambda console, locate the "hopper" function and add test input

    {
        "messageType":"pageUrl",
        "url":"http://abc.com"
    }

7. Run "Test" for the AWS Lambda function
8. Check the CloudWatch logs for the output - you should see something like this:
    You should see a number of 'pageUrl' entries, without any errors.


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
                        "arn:aws:dynamodb:ap-southeast-2:334633661752:table/HopperRuntime"
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
                        "arn:aws:kinesis:ap-southeast-2:334633661752:stream/HopperQueue"
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
                    "Resource": "arn:aws:lambda:ap-southeast-2:334633661752:function:hopper"
                },
                {
                    "Effect": "Allow",
                    "Action": "kinesis:ListStreams",
                    "Resource": "arn:aws:kinesis:ap-southeast-2:334633661752:stream/*"
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
                        "arn:aws:lambda:ap-southeast-2:334633661752:event-source-mappings:*"
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
                    "Resource": "arn:aws:lambda:ap-southeast-2:334633661752:function:hopper"
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "iam:PassRole"
                    ],
                    "Resource": "arn:aws:iam::334633661752:role/hopper-runtime"
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
                        "arn:aws:dynamodb:ap-southeast-2:334633661752:table/HopperRuntime"
                    ]
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "kinesis:DescribeStream"
                    ],
                    "Resource": [
                        "arn:aws:kinesis:ap-southeast-2:334633661752:stream/HopperQueue"
                    ]
                }
            ]
        }

