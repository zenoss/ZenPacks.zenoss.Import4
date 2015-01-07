##############################################################################
#
# Copyright (C) Zenoss, Inc. 2014-2015, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

import argparse
from ZenPacks.zenoss.Import4.migration import MigrationBase


def init_command_parser(subparsers):
    perf_parser = subparsers.add_parser('perf', help='migrate performance data')
    return perf_parser


class Migration(MigrationBase):
    pass
