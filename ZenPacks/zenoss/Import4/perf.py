import argparse
from ZenPacks.zenoss.Import4.migration import MigrationBase


def init_command_parser(subparsers):
    perf_parser = subparsers.add_parser('perf', help='migrate performance data')
    return perf_parser


class Migration(MigrationBase):
    pass
