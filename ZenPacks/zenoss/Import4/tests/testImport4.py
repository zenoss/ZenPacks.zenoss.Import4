#!/usr/bin/env python
##############################################################################
#
# Copyright (C) Zenoss, Inc. 2014-2015, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

import argparse
import sys
import traceback
import logging

from ZenPacks.zenoss.Import4 import migration, model, events, perf

log = logging.getLogger('import4')

def run_migration(migration_class, args):
    # The main control running a migration process
    _migration = migration_class(args, progress_report_callback)

    # Run pname functions
    try:
        log.info('Executing %s', args.pname)
        {
            'check': _migration.prevalidate,
            'verify': _migration.postvalidate,
            'import': _migration.importFunc
        }[args.pname]()

    except migration.ImportError as err:
        log.error(err.error_string)
        log.exception(err)
        exit(err.return_code)

    except Exception as e:
        # unrecognized exception
        log.error("Unknown exception --- ")
        log.exception(e)
        exit(migration.ExitCode.UNKNOWN)

    # all finished successfully
    log.info('%s done!', args.pname)
    exit(migration.ExitCode.SUCCESS)


def progress_report_callback(msg):
    sys.stdout.write(msg)
    sys.stdout.flush()


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Import data from a 4.x Zenoss instance. These imports are destructive - "
            "the relevant datastores on this instance will be destroyed, and the 4.x "
            "data imported in its place.\n\n"
        )
    )
    # add the global options
    migration.MigrationBase.init_command_parser(parser)

    subparsers = parser.add_subparsers(help='Group of migration functions')
    for module in (model, events, perf):
        m_name = module.__name__.split(".")[-1]
        m_parser = subparsers.add_parser(m_name, description='Tool to migrate %s data' % m_name)
        m_subparser = m_parser.add_subparsers()
        # Add action-specific parsers
        check_parser = m_subparser.add_parser('check', description='Run pre-validation on 4x backup artifact prior to import')
        check_parser.set_defaults(pname='check')
        import_parser = m_subparser.add_parser('import', description='Perform an import')
        import_parser.set_defaults(pname='import')
        verify_parser = m_subparser.add_parser('verify', description='Run post-validation on new system')
        verify_parser.set_defaults(pname='verify')
        module.Migration.init_command_parser(m_parser)
        module.Migration.init_command_parsers(check_parser, verify_parser, import_parser)
        m_parser.set_defaults(functor=lambda args, mclass=module.Migration: run_migration(mclass, args))

    args = parser.parse_args()

    return args


def main():
    args = parse_args()
    args.functor(args)

if __name__ == "__main__":
	args = parse_args()
	_migrate = model.Migration(args, progress_report_callback)
	_migrate.reportError('Test', 'This')
	_migrate.reportWarning('Test', 'That')
