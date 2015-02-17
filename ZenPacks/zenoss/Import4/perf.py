##############################################################################
#
# Copyright (C) Zenoss, Inc. 2014-2015, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

import os
import sys
import subprocess
import re
import time

from ZenPacks.zenoss.Import4.migration import MigrationBase, ImportError

# some common constants shared among the py and bash scripts
_check_tag = '[Check] '
_stderr_tag = '[STDERR] '
_import_prefix = 'Perf: '

_import4_vol = '/import4'
_import4_pkg = '/import4/pkg'
_import4_pkg_bin = '/import4/pkg/bin'

_tasks_Q = '%s/Q.tasks' % _import4_vol
_jobs_Q = '%s/Q.jobs' % _import4_vol
_tsdb_Q = '%s/Q.tsdb' % _import4_vol

_jobs_done = '%s/.done' % _jobs_Q
_tsdb_done = '%s/.done' % _tsdb_Q


class Results(object):
    RUNTIME_ERROR = 'PERF_MIGRATION_RUNTIME_ERROR'
    COMMAND_ERROR = 'PERF_MIGRATION_COMMAND_ERROR'
    UNTAR_FAIL = 'PERF_MIGRATION_UNTAR_FAILED'
    INVALID = 'PERF_MIGRATION_INVALID'
    WARNING = 'PERF_MIGRATION_WARNING'
    FAILURE = 'PERF_MIGRATION_FAILURE'
    SUCCESS = 'PERF_MIGRATION_SUCCESS'


class PerfDataImportError(ImportError):
    def __init__(self, error_string, return_code):
        super(PerfDataImportError, self).__init__(error_string, return_code)


def init_command_parser(subparsers):
    perf_parser = subparsers.add_parser('perf', help='migrate performance data')
    # TBD collect the rrd top and perf data top
    perf_parser.add_argument('rrd_dir',
                             help="Top directory for a 4.x rrd tree")
    perf_parser.add_argument('-p', '--perf_top', dest='perf_top', default="",
                             help="Parent directory of the rrd trees")
    return perf_parser


class Migration(MigrationBase):
    def __init__(self, args, progressCallback):
        # common setup
        super(Migration, self).__init__(args, progressCallback)
        self.rrd_dir = os.path.abspath(args.rrd_dir)
        if not os.path.exists(_import4_vol):
            print _import_prefix + "%s does not exist" % _import4_vol
            raise PerfDataImportError(Results.RUNTIME_ERROR, -1)
        # for the imp4mariadb and imp4opentsdb services
        if (not os.path.exists(_import4_pkg) or
           not os.path.exists(_import4_pkg_bin)):
            # this call should not execute under '/import4/pkg'
            # instead, via <zenpack_path>/bin/import4
            _rc = subprocess.call(["%s/install_pkg.sh" % sys.path[0]],
                                  shell=True, stderr=subprocess.STDOUT)
            if _rc > 0:
                raise PerfDataImportError(Results.RUNTIME_ERROR, _rc)
        if not os.path.exists('%s/imp4mariadb.sh' % _import4_pkg_bin):
            raise PerfDataImportError(Results.RUNTIME_ERROR, _rc)
        if not os.path.exists('%s/imp4opentsdb.sh' % _import4_pkg_bin):
            raise PerfDataImportError(Results.RUNTIME_ERROR, _rc)

    def prevalidate(self):
        # check if the rrd_dir is valid
        if not os.path.exists(self.rrd_dir):
            print _import_prefix + "%s does not exist" % self.rrd_dir
            raise PerfDataImportError(Results.INVALID, -1)
        # TBD:what other easy checks can we do??

    def postvalidate(self):
        self.__NOT_YET__()
        # not doing anything for now
        return

    def wipe(self):
        self.__NOT_YET__()
        # need to place a command tag for imp4opentsdb service
        # to clean up the backend
        return

    def doImport(self):
        # dispatch the work into task lists
        _args = ["%s/dispatch.sh" % sys.path[0], self.rrd_dir, _tasks_Q]
        _rc = subprocess.call(
            _args, shell=False, stderr=subprocess.STDOUT)

        if _rc != 0:
            raise PerfDataImportError(Results.COMMAND_ERROR, _rc)
        self.reportProgress("rrd files dispatched to tasks")

        # polling the task files and job/.done to report progress
        # the output pattern is hardcoded in the perf_progress.sh
        _repattern = re.compile('T:(\d+) S:(\d+) C:(\d+) D:(\d+) P:(\d+)')

        # run until _done == _tasks
        try:
            # wait 10 seconds before each check
            while True:
                self.reportProgress(".")
                time.sleep(10)
                _progress = subprocess.check_output(["%s/perf_progress.sh" % sys.path[0]])
                _num = _repattern.search(_progress)
                if _num:
                    self.reportProgress(_progress)
                    _tno = int(_num.group(1))
                    _dno = int(_num.group(4))
                    _cents = int(_num.group(5))
                    self.reportProgress("[%s/%s] %s%%" %
                                        (_dno, _tno, _cents))
                    if _dno == _tno:
                        break
                else:
                    # cannot recognize the progress output string
                    raise PerfDataImportError(Results.COMMAND_ERROR, -1)
        except:
            print sys.exc_info()[0]
            raise PerfDataImportError(Results.FAILURE, -1)

        self.reportProgress("Performance data import complete!")
        return

    def reportProgress(self, raw_line):
        _msg = raw_line
        if _msg:
            _msg = _import_prefix + '%s\n' % _msg.strip()
            super(Migration, self).reportProgress(_msg)
        return
