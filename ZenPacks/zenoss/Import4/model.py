import argparse
from migration import MigrationBase


def init_command_parser(subparsers):
    model_parser = subparsers.add_parser('model', help='migrate model data')
    return model_parser


class Migration(MigrationBase):
    pass
