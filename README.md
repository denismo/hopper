Hopper
======

Hopper is a message passing framework that allows writing message-driven distributed applications in Python, deployed on AWS Lambda.
It abstract away the details of sending messages, queueing, invoking the right handler, correlating, and dealing with errors, letting you focus on the business logic of data processing and transformations.
It is inspired by [Akka actors](http://doc.akka.io/docs/akka/snapshot/intro/what-is-akka.html), 
[AWSLabs Chalice](https://github.com/awslabs/chalice), [Apache Storm](http://storm.apache.org/).

Note: this project is in Proof-of-concept state. I do not recommend anyone using it, but please do evaluate, and provide feedback if you find it interesting. 
----

Usage scenarios
===============
- A web crawler
- Real-time Analytics
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

Chain and Fork-join (pending)
-----
Combining input from Chalice, you can create a one-way pipeline of asynchronous processing.

Example is a real-time analytics use case, where page view requires additional resolution such as geo-ip lookup and user agent,
both of which run in parallel, until the results are provided to the final handler which stores it in a DB.

The handlers are just normal Python functions (or Python lambdas), and they will be invoked in separate Lambda invocations, ensuring the pipeline is non-blocking.

```python
# pageView?url=...
@app.route('/pageView')
def pageView():
    url = app.current_request.query_params['url]
    # Publishes a message into the pipeline
    # which will be processed by geoIPLookup and resolveUserAgent (in parallel)
    # and then the messages of both will be dispatched (combined) to enrichedPageView
    # which can merge them together  
    context.publish(dict(messageType='pageView', url=url))
        # "fork" tells the handlers to run in parallel 
        .fork() \
        # "then" will run after handle asynchronously using another Lambda invocation
        .handle(geoIPLookup).then(...) \
        # another "handle" will run in parallel with the handle-then above
        .handle(resolveUserAgent) \
        # join will delay the final handlers until all above paths produced results and 
        # group them by parentMessageID into one message handled by "enrichedPageView"
        .join(enrichedPageView)

# Alternative to .join - collect all message which have the same parent 'pageView'
@context.join(parentMessage='pageView')
def collectPageViews(msgs):
    ...
```

Pipeline (pending)
-----------------
You can also define a standalone pipeline with pre-defined source (ala Spark Streaming).

Example below will listen on Kinesis HopperQueue for any messages match them to handlers (ala switch-case), processing sequentially (but asynchronously) until
there are no more messages. Similar for Fork-Join, the handlers in this case are just normal Python functions (or Python lambdas), 
and they will be invoked in separate Lambda invocations, ensuring the pipeline is non-blocking.

This code will execute at top-level, inside of the "main" function.
```python
context.source(sources.kinesis('HopperQueue')) \
    .case('pageView', context.fork() \
        # "then" will run after handle
        .handle(geoIPLookup).then(...) \
        # another "handle" will run in parallel with the handle-then above
        .handle(resolveUserAgent) \        
        # join will delay the final handlers until all above paths produced results and 
        # group them by parent message ID into one message handled by "enrichedPageView"
        .join(enrichedPageView)
    ) 
    .case('linkClick', actionHandler) \
    .other(defaultHandler)
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
