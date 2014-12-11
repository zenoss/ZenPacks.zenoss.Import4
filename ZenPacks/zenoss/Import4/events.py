import argparse
from ZenPacks.zenoss.Import4.migration import MigrationBase


def get_command(subparsers):
    events_parser = subparsers.add_parser('events')
    return events_parser


class Migration(MigrationBase):
    pass