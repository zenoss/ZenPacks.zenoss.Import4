##############################################################################
#
# Copyright (C) Zenoss, Inc. 2014-2015, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

# BaseTestCase is a subclass of ZopeTestCase which is ultimately a subclass of
# Python's standard unittest.TestCase. Because of this the following
# documentation on unit testing in Zope and Python are both applicable here.
#
# Python Unit testing framework
# http://docs.python.org/library/unittest.html
#
# Zope Unit Testing
# http://wiki.zope.org/zope2/Testing

import argparse
import sys
from StringIO import StringIO

from Products.ZenTestCase.BaseTestCase import BaseTestCase
from ZenPacks.zenoss.Import4 import migration, model, events, perf


# Testing the import4 module.
# All functional tests will be done at end-to-end configuration.
# The tests here covers cherry-picked areas for further code coverage.

msg_buf = ''


# save the reported msg somewhere
def test_report_callback(msg):
    msg_buf = msg
    sys.stdout.write(msg_buf)
    sys.stdout.flush()


def parse_args(args=None):
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

    args = parser.parse_args(args=args)

    return args


class TestImport4(BaseTestCase):
    def afterSetUp(self):
        super(TestImport4, self).afterSetUp()
        self.args = parse_args(['perf', 'check'])
        self.imp4 = None

    def beforeTearDown(self):
        super(TestImport4, self).beforeTearDown()
        self.imp4 = None


class TestImport4Migrate(TestImport4):
    def afterSetUp(self):
        super(TestImport4Migrate, self).afterSetUp()
        self.args = parse_args(['perf', 'check'])
        self.imp4 = migration.MigrationBase(self.args, test_report_callback)

    def _exec_cmd(self, cmd, **kwargs):
        print 'cmd:' + cmd
        print kwargs
        out_s = sys.stdout
        self.out = StringIO()
        sys.stdout = self.out
        self.imp4.exec_cmd(cmd, **kwargs)
        sys.stdout = out_s
        print self.out.getvalue()

    def test_init(self):
        self.imp4 = migration.MigrationBase(self.args, test_report_callback)
        self.assertNotEqual(self.imp4, None)

    def test_exec_cmd(self):
        _test_re = '123'
        _test_str = '[Key%s]: This is string' % _test_re
        _cmd_str = 'echo "%s"' % _test_str
        self._exec_cmd(_cmd_str)
        self.assertTrue(True)

    def test_report_status(self):
        _test_re = '123'
        _test_str = '[Key%s]: This is string\n' % _test_re
        _cmd_str = 'echo "%s"' % _test_str
        self._exec_cmd(_cmd_str, status_key='TestStatus', status_max=3, status_re=_test_re, to_log=True)
        self.assertTrue('{"imp4_status": {"%s": %d}}' % ('TestStatus', 1) in self.out.getvalue())


class TestImport4Event(TestImport4):
    def afterSetUp(self):
        super(TestImport4Event, self).afterSetUp()
        self.imp4 = events.Migration(self.args, test_report_callback)

    def test_init(self):
        self.args = parse_args(['events', 'check'])
        self.imp4 = events.Migration(self.args, test_report_callback)
        self.assertNotEqual(self.imp4, None)


class TestImport4Perf(TestImport4):
    def afterSetUp(self):
        super(TestImport4Perf, self).afterSetUp()
        self.imp4 = perf.Migration(self.args, test_report_callback)

    def test_init(self):
        self.args = parse_args(['perf', 'check'])
        self.imp4 = perf.Migration(self.args, test_report_callback)
        self.assertNotEqual(self.imp4, None)


class TestImport4Model(TestImport4):
    def afterSetUp(self):
        super(TestImport4Model, self).afterSetUp()
        self.imp4 = model.Migration(self.args, test_report_callback)

    def test_init(self):
        self.args = parse_args(['model', 'check'])
        self.imp4 = model.Migration(self.args, test_report_callback)
        self.assertNotEqual(self.imp4, None)


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()

    # Add your BaseTestCase subclasses here to have them executed.
    suite.addTest(makeSuite(TestImport4Migrate))
    suite.addTest(makeSuite(TestImport4Event))
    suite.addTest(makeSuite(TestImport4Perf))
    suite.addTest(makeSuite(TestImport4Model))

    return suite
