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

from ZenPacks.zenoss.Import4.migration import MigrationBase, ImportError, Config

# some common constants shared among the py and bash scripts
_check_tag = '[Check] '
_stderr_tag = '[STDERR] '
_import_prefix = 'Perf: '

_import4_vol = Config.volume
_import4_pkg = Config.pkgPath
_import4_pkg_bin = Config.pkgBinPath

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


class Migration(MigrationBase):

    importFuncs = {}

    def __init__(self, args, progressCallback):
        # common setup
        super(Migration, self).__init__(args, progressCallback)

        # check and install the scripts for mariadb and opentsdb services
        self.rrd_dir_arg = args.rrd_dir
        self.rrd_dir = os.path.abspath(args.rrd_dir)
        self.skip_scan = args.skip_scan
        self.files_no = 0

        # if self.perf_top does not exist, derive it from rrd_dir
        if args.perf_top:
            self.perf_top = os.pat.abspath(args.perf_top)
        else:
            _idx = self.rrd_dir.find("Devices/")
            self.perf_top = self.rrd_dir[:_idx+7]

        self.data_checked = '%s/PERF_CHECKED' % self.tempDir
        self.data_migrated = '%s/PERF_MIGRATED' % self.tempDir

        if not os.path.exists(_import4_vol):
            self.reportProgress("%s does not exist." % _import4_vol)
            raise PerfDataImportError(Results.RUNTIME_ERROR, -1)

        # always copy the small pkg for the imp4mariadb and imp4opentsdb services
        # this call should not execute under '/import4/pkg'
        # instead, via <zenpack_path>/bin/import4
        '''
        # this is already done before the service starts
        _rc = subprocess.call(["%s/install_pkg.sh" % self.binpath,
                              shell=True, stderr=subprocess.STDOUT)
        if _rc > 0:
            raise PerfDataImportError(Results.RUNTIME_ERROR, _rc)
        '''

        if not os.path.exists('%s/imp4mariadb.sh' % _import4_pkg_bin):
            raise PerfDataImportError(Results.RUNTIME_ERROR, -1)
        if not os.path.exists('%s/imp4opentsdb.sh' % _import4_pkg_bin):
            raise PerfDataImportError(Results.RUNTIME_ERROR, -1)

    @staticmethod
    def init_command_parser(m_parser):
        # if rrd_dir is specified, it will only import the selected
        m_parser.add_argument('--rrd_dir', dest='rrd_dir', default="",
                                help="Top directory for a existing 4.x rrd tree")
        m_parser.add_argument('-t', '--perf_top', dest='perf_top', default="",
                                help="Parent directory of the rrd trees")
        m_parser.add_argument('-n', '--skip-scan', action='store_true', dest='skip_scan', default=False,
                                help="Skip the scanning of rrdfiles' content")

    @classmethod
    def init_command_parsers(cls, check_parser, verify_parser, import_parser):
        super(Migration, cls).init_command_parsers(check_parser, verify_parser, import_parser)

    def _setup_rrd_dir(self):
        if not self.rrd_dir_arg:
            self.rrd_dir = '%s/Devices' % self.perf_dir
            self.perf_top = self.rrd_dir
        else:
            # else, rrd_dir is the one derived from provided rrd_dir_arg
            self.reportProgress("Use %s provided ..." % self.rrd_dir)

        # check if the rrd_dir is valid
        if not os.path.exists(self.rrd_dir):
            self.reportProgress("%s does not exist. Need to extract the backup file first." % self.rrd_dir)
            raise PerfDataImportError(Results.INVALID, -1)

    def _get_rrd_list(self):
        try:
            _rrd_list = '%s/rrd.list' % self.perf_dir
            _cmd = 'find %s -type f -name "*.rrd"' % self.rrd_dir

            with open(_rrd_list, "w") as _rlfile, open('%s.err' % _rrd_list, "w") as _errfile:
                subprocess.check_call(_cmd, shell=True, stdout=_rlfile, stderr=_errfile)

            _cmd = 'cat %s | wc -l' % _rrd_list
            self.files_no = int(subprocess.check_output('cat %s | wc -l' % _rrd_list, shell=True))
        except Exception as e:
            print e
            raise PerfDataImportError(Results.INVALID, -1)
        self.reportProgress("rrd files to work on:%s" % self.files_no)
        return _rrd_list

    def prevalidate(self):
        self._setup_rrd_dir()
        _rrd_list = self._get_rrd_list()

        # this allows an user to skip the lengthy validation
        # that was validated offline before
        if self.skip_scan:
            self.reportProgress("rrd scanning skip option specified - skipped")
            # mark the checked file
            with open(self.data_checked, 'a'):
                pass
            return

        # here we do a single-process check of the rrdfiles
        # we go thru each rrdfile and do a dryrun
        self.reportProgress("Scanning rrdfiles ...")
        _total_dr = 0
        _total_dp = 0
        _total_ds = 0
        _i = 0
        try:
            with open(_rrd_list, "r") as f:
                for _aline in f:
                    _one_rrd = _aline.strip()
                    _i = _i+1
                    self.reportProgress("%s ...[%d/%d]" % (_one_rrd, _i, self.files_no))
                    _cmd = '%s/rrd2tsdb.py -t -p "%s" "%s"' % (Config.pkgPath, self.perf_top, _one_rrd)
                    _result = subprocess.check_output(_cmd, shell=True, stderr=None).strip()
                    self.reportProgress("%s datapoints..." % _result)
                    _total_dp += int(_result)
                    if int(_result):
                        _total_ds += 1
                    else:
                        # check if the 0 results from a dup derived in rrd file
                        # remove .rrd
                        if os.path.isfile("%s_GAUGE.rrd" % _one_rrd[:-4]):
                            self.reportProgress("Info: DERIVE type dup'ed into GAUGE")
                            _total_dr += 1
                        else:
                            self.reportProgress("Warn: no datapoint found, all NaN?")
        except Exception as e:
            print e
            raise PerfDataImportError(Results.INVALID, -1)

        self.reportProgress("DS#: %d" % _total_ds)
        self.reportProgress("DR#: %d" % _total_dr)
        self.reportProgress("DP#: %d" % _total_dp)

        # mark the checked file
        with open(self.data_checked, 'a'):
            pass
        return

    def postvalidate(self):
        self._setup_rrd_dir()
        if not os.path.isfile(self.data_migrated):
            self.reportProgress("Error: Performance data not imported yet")
            raise PerfDataImportError(Results.INVALID, -1)

        # self.password is either '' or something
        if not self.user:
            self.reportProgress("Error: username not provided")
            raise PerfDataImportError(Results.COMMAND_ERROR, -1)

        _rrd_list = self._get_rrd_list()
        try:
            _no = 0
            _eno = 0
            with open(_rrd_list, "r") as f:
                for _aline in f:
                    _one_rrd = _aline.strip()
                    self.reportProgress("%s ..." % _one_rrd)

                    if self.user and (self.password != ""):
                        _cre = "-v %s:%s" % (self.user, self.password)
                    elif self.user:
                        _cre = "-v %s" % self.user
                    else:
                        _cre = ""

                    _cmd = '%s/rrd2tsdb.py %s -p "%s" "%s"' % (
                        Config.pkgPath, _cre, self.perf_top, _one_rrd)
                    _result = subprocess.call(_cmd, shell=True, stdout=None, stderr=None)
                    if _result == 0:
                        _no += 1
                        self.reportProgress("%s:. [%d/%d] verified" % (_one_rrd, _no, self.files_no))
                    else:
                        _eno += 1
                        self.reportProgress("%s:. [%d/%d] Error..." % (_one_rrd, _eno, self.files_no))
        except Exception as e:
            print e
            raise PerfDataImportError(Results.INVALID, -1)

        return

    def wipe(self):
        # self.__NOT_YET__()
        # it is decided that we don't wipe the pre-existing opentsdb
        # This allows incremental importing of selected devices
        return

    def doImport(self):
        self._setup_rrd_dir()

        if not os.path.exists(self.data_checked):
            self.reportProgress("rrdfiles not validated yet. Run `perf check` command first.")
            raise PerfDataImportError(Results.INVALID, -1)

        if os.path.isfile(self.data_migrated):
            os.remove(self.data_migrated)

        # cleanup the shared directories for the services
        _args = ["%s/cleanup_jobs.sh" % self.binpath]
        _rc = subprocess.call(
            _args, shell=False, stderr=subprocess.STDOUT)
        if _rc != 0:
            raise PerfDataImportError(Results.COMMAND_ERROR, _rc)

        # setup the fixed PERFTOP file for the parallel services
        text_file = open("/import4/Q.tasks/PERFTOP", "w")
        text_file.write("%s" % self.perf_top)
        text_file.close()

        # dispatch the work into task lists
        _args = ["%s/dispatch.sh" % self.binpath, self.rrd_dir, _tasks_Q]
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
                # self.reportProgress(".")
                time.sleep(10)
                _progress = subprocess.check_output(["%s/perf_progress.sh" % self.binpath])
                _num = _repattern.search(_progress)
                if _num:
                    self.reportProgress(_progress)
                    _tno = int(_num.group(1))
                    _cno = int(_num.group(3))
                    _dno = int(_num.group(4))
                    _cents = int(_num.group(5))
                    self.reportProgress("[%s/%s] %s%%" %
                                        (_dno, _tno, _cents))
                    if (_dno == _tno) and (_cno == _tno):
                        break
                else:
                    # cannot recognize the progress output string
                    raise PerfDataImportError(Results.COMMAND_ERROR, -1)
        except:
            print sys.exc_info()[0]
            raise PerfDataImportError(Results.FAILURE, -1)

        with open(self.data_migrated, 'a'):
            pass

        self.reportProgress("Performance data import complete!")
        return

    def reportProgress(self, raw_line):
        _msg = raw_line
        if _msg:
            _msg = _import_prefix + '%s\n' % _msg.strip()
            super(Migration, self).reportProgress(_msg)
        return
