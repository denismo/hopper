import boto3

def _updateTrigger(cfg, enabled=False):
    """Disables Kinesis/Lambda trigger"""
    triggerID = _getTriggerID(cfg)
    print('TriggerID', triggerID)
    if triggerID is not None:
        awslambda = boto3.client("lambda", region_name=cfg.get('region'))
        awslambda.update_event_source_mapping(
            UUID=triggerID, 
            FunctionName=cfg.get('function_name'),
            Enabled=enabled)

def _createTrigger(cfg):
    triggerID = _getTriggerID(cfg)
    if triggerID is None:
        awslambda = boto3.client("lambda", region_name=cfg.get('region'))
        awslambda.create_event_source_mapping(
            EventSourceArn='arn:aws:kinesis:%s:%s:stream/%s' % (cfg.get('region'), _getAWSAccountId(cfg), cfg.get('kinesis-stream')),
            FunctionName=cfg.get('function_name'),
            Enabled=False,
            BatchSize=100,
            StartingPosition='LATEST'            
        )

def _getTriggerID(cfg):
    try:
        awslambda = boto3.client("lambda", region_name=cfg.get('region'))
        mappings = awslambda.list_event_source_mappings(
                EventSourceArn='arn:aws:kinesis:%s:%s:stream/%s' % (cfg.get('region'), _getAWSAccountId(cfg), cfg.get('kinesis-stream')),
                FunctionName=cfg.get('function_name')                    
        )    
        if mappings is not None and 'EventSourceMappings' in mappings:
            print(mappings)
            return mappings['EventSourceMappings'][0]['UUID']
        else:
            return None
    except:        
        logging.exception('Unable to determine trigger ID')
        return None

def _getAWSAccountId(cfg):
    return  boto3.client('kinesis', region_name=cfg.get('region')).describe_stream(StreamName=cfg.get('kinesis-stream'))['StreamDescription']['StreamARN'].split(':')[4]
    # return boto3.client('iam').list_users(MaxItems=1)["Users"][0]["Arn"].split(':')[4]    

def _createKinesis(cfg):
    kinesis = boto3.client('kinesis', region_name=cfg.get('region'))
    try:
        kinesis.describe_stream(StreamName=cfg.get('kinesis-stream'))
    except ResourceNotFoundException as rnfe:
        kinesis.create_stream(ShartCount=cfg.get('kinesis-shard-count', 1), StreamName=cfg.get('kinesis-stream'))

def _createDynamoDB(cfg):
    dynamo = boto3.client("dynamodb", region_name=cfg.get('region'))
    try:
        dynamo.describe_table(TableName=cfg.get('dynamodb-table'))
    except ResourceNotFoundException as rnfe:
        dynamo.create_table(TableName=cfg.get('dynamodb-table'),
            AttributeDefinitions=[
                {
                    'AttributeName': 'Object',
                    'AttributeType': 'S'
                }],
            KeySchema=[
                {
                    'AttributeName': 'Object',
                    'KeyType': 'HASH'
                },
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 1,
                'WriteCapacityUnits': 1
            },)
    
    # Wait for table to be created
    description = dynamo.describe_table(TableName=cfg.get('dynamodb-table'))
    iter = 0
    while description["Table"]["TableStatus"] != "ACTIVE":
        print "Waiting for %s to be created: %d..." % (cfg.get('dynamodb-table'), iter)
        iter += 1
        sleep(1)
        description = connection.describe_table(TableName=cfg.get('dynamodb-table'))

    # Reset request count and termnation status
    table = boto3.resource('dynamodb', region_name=cfg.get('region')).Table(cfg.get('dynamodb-table'))
    table.update_item(
        Key={
            'Object': 'RuntimeState',
        },
        AttributeUpdates={
            'RequestCounter': {'Action': 'ADD', 'Value': 1},                
            'Terminated': {'Action': 'PUT', 'Value': False}                
        }
    )    
    