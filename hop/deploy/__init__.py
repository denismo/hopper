from __future__ import print_function
from aws_lambda import build, deploy
from aws_lambda.helpers import read
from .aws import _updateTrigger, _createKinesis, _createDynamoDB, _createTrigger 
import os
import boto3
import yaml

def doDeploy():
    """Deploys the lambda package and associated resources, based on the configuration file config.yaml supplied in the root directory"""
    packageDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.path.pardir, os.path.pardir)
    path_to_config_file = os.path.join(packageDir, 'config.yaml')
    cfg = read(path_to_config_file, loader=yaml.load)

    # build(packageDir)
    print('Deploying Lambda function')
    deploy(packageDir, subfolders={'hop','examples'})

    print('Disabling trigger')
    _updateTrigger(cfg, enabled=False)
    print('Creating Kinesis stream')
    _createKinesis(cfg)
    print('Creating DynamoDB table')
    _createDynamoDB(cfg)
    print('Creating trigger')
    _createTrigger(cfg)
    print('Enabling trigger')
    _updateTrigger(cfg, enabled=True)    

