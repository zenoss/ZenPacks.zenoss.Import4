import argparse
from ZenPacks.zenoss.Import4.migration import MigrationBase


def get_command(subparsers):
    perf_parser = subparsers.add_parser('perf')
    return perf_parser


class Migration(MigrationBase):
    pass