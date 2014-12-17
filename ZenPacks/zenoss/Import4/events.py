import argparse
from ZenPacks.zenoss.Import4.migration import MigrationBase


def get_command(subparsers):
    events_parser = subparsers.add_parser('events', help='migrate event data')
    return events_parser


class Migration(MigrationBase):
    pass
