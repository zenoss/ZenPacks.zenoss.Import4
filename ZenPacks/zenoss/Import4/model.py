##############################################################################
#
# Copyright (C) Zenoss, Inc. 2014-2015, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

import argparse
from migration import MigrationBase


def init_command_parser(subparsers):
    model_parser = subparsers.add_parser('model', help='migrate model data')
    return model_parser


class Migration(MigrationBase):
    pass
