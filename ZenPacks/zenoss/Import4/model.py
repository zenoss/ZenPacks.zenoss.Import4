import argparse
from migration import MigrationBase


class Migration(MigrationBase):
    pass


def get_command(subparsers):
    model_parser = subparsers.add_parser('model')
    return model_parser