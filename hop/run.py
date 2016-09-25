import os
import click
import logging
from deploy import doDeploy

logging.getLogger('pip').setLevel(logging.CRITICAL)

@click.group()
def cli():
    pass

@click.command(help="Deploy Hop package")
def deploy():
    doDeploy()

if __name__ == '__main__':
    cli.add_command(deploy)
    cli()
