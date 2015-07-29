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

from ZenPacks.zenoss.Import4.migration import MigrationBase, ImportError, Config, ExitCode, log, Imp4Meta

# some common constants shared among the py and bash scripts
_import4_vol = Config.volume
_import4_pkg = Config.pkgPath
_import4_pkg_bin = Config.pkgBinPath

_tasks_Q = '%s/Q.tasks' % _import4_vol
_jobs_Q = '%s/Q.jobs' % _import4_vol
_tsdb_Q = '%s/Q.tsdb' % _import4_vol

_jobs_done = '%s/.done' % _jobs_Q
_tsdb_done = '%s/.done' % _tsdb_Q


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

        # check runtime environment
        if not os.path.exists(_import4_vol):
            log.error("%s does not exist.", _import4_vol)
            raise ImportError(ExitCode.RUNTIME_ERROR)
        if not os.path.exists('%s/imp4mariadb.sh' % _import4_pkg_bin):
            log.error("%s/imp4mariadb.sh does not exist.", _import4_pkg_bin)
            raise ImportError(ExitCode.RUNTIME_ERROR)
        if not os.path.exists('%s/imp4opentsdb.sh' % _import4_pkg_bin):
            log.error("%s/imp4opentsdb.sh does not exist.", _import4_pkg_bin)
            raise ImportError(ExitCode.RUNTIME_ERROR)

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
            log.info("Use %s provided ..." % self.rrd_dir)

        log.info("RRDTree:%s..." % self.rrd_dir)
        # check if the rrd_dir is valid
        if not os.path.exists(self.rrd_dir):
            log.error("%s does not exist. Need to extract the backup file first." % self.rrd_dir)
            self.reportError('perf_import', 'Performance data not extracted')
            raise ImportError(ExitCode.INVALID)

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
            raise ImportError(ExitCode.INVALID)
        log.info("rrd files to work on:%s" % self.files_no)
        return _rrd_list

    def prevalidate(self):
        self._setup_rrd_dir()
        _rrd_list = self._get_rrd_list()

        self.reportMetaData(Imp4Meta.num_perfrrd, 0, self.files_no)
        self.reportMetaData(Imp4Meta.num_perftsdb, 0, self.files_no)
        # self.reportMetaData(Imp4Meta.num_perf, 0, self.files_no)

        # this allows an user to skip the lengthy validation
        # that was validated offline before
        if self.skip_scan:
            log.info("rrd scanning skip option specified - skipped")
            # mark the checked file
            with open(self.data_checked, 'a'):
                pass
            return

        # here we do a single-process check of the rrdfiles
        # we go thru each rrdfile and do a dryrun
        log.info("Scanning rrdfiles ...")
        _total_dr = 0
        _total_dp = 0
        _total_ds = 0
        _i = 0
        try:
            with open(_rrd_list, "r") as f:
                for _aline in f:
                    _one_rrd = _aline.strip()
                    _i = _i+1
                    log.info("%s ...[%d/%d]" % (_one_rrd, _i, self.files_no))
                    _cmd = '%s/rrd2tsdb.py -t -p "%s" "%s"' % (Config.pkgPath, self.perf_top, _one_rrd)
                    _result = subprocess.check_output(_cmd, shell=True, stderr=None).strip()
                    log.info("%s datapoints..." % _result)
                    _total_dp += int(_result)
                    if int(_result):
                        _total_ds += 1
                    else:
                        # check if the 0 results from a dup derived in rrd file
                        # remove .rrd
                        if os.path.isfile("%s_GAUGE.rrd" % _one_rrd[:-4]):
                            log.info("DERIVE type dup'ed into GAUGE")
                            _total_dr += 1
                        else:
                            log.warning("no datapoint found, all NaN?")
                            self.reportWarning('perf_import', 'No datapoint value found in %s' % _one_rrd)
        except Exception as e:
            print e
            self.reportError('perf_import', 'Performance data validation failed')
            raise ImportError(ExitCode.INVALID)

        # mark the checked file
        with open(self.data_checked, 'a'):
            pass
        return

    def postvalidate(self):
        self._setup_rrd_dir()
        if not os.path.isfile(self.data_migrated):
            log.error("Performance data not imported yet")
            self.reportError('perf_import', 'Performance data not imported yet')
            raise ImportError(ExitCode.INVALID)

        # output the dimension for the post validation
        self.reportMetaData(Imp4Meta.num_perf, 0, self.files_no)

        # self.password is either '' or something
        if not self.user:
            log.error("username not provided")
            self.reportError('perf_import', 'Username and password required for performance postvalidation')
            raise ImportError(ExitCode.CMD_ERROR)

        _rrd_list = self._get_rrd_list()
        try:
            _no = 0
            _eno = 0
            with open(_rrd_list, "r") as f:
                for _aline in f:
                    _one_rrd = _aline.strip()
                    log.info("%s ..." % _one_rrd)

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
                        log.info("%s:. [%d/%d] verified..." % (_one_rrd, _no, self.files_no))
                    else:
                        _eno += 1
                        log.warning("%s:. [%d/%d] Error detected..." % (_one_rrd, _eno, self.files_no))
                        self.reportWarning('perf_import', 'Error detected in performance data in %s' % _one_rrd)
                    self.reportStatus(Imp4Meta.num_perf, _no+_eno)

        except Exception as e:
            log.exceptioni(e)
            raise ImportError(ExitCode.INVALID)

        return

    def wipe(self):
        # self.__NOT_YET__()
        # it is decided that we don't wipe the pre-existing opentsdb
        # This allows incremental importing of selected devices
        return

    def doImport(self):
        self._setup_rrd_dir()

        if not os.path.exists(self.data_checked):
            log.error("rrdfiles not validated yet. Run `perf check` command first.")
            self.reportError('perf_import', 'Perfmance RRD files not validated')
            raise ImportError(ExitCode.INVALID)

        if os.path.isfile(self.data_migrated):
            os.remove(self.data_migrated)

        # cleanup the shared directories for the services
        _args = ["%s/cleanup_jobs.sh" % _import4_pkg_bin]
        _rc = subprocess.call(
            _args, shell=False, stderr=subprocess.STDOUT)
        if _rc != 0:
            raise ImportError(ExitCode.CMD_ERROR)

        # setup the fixed PERFTOP file for the parallel services
        text_file = open("/import4/Q.tasks/PERFTOP", "w")
        text_file.write("%s" % self.perf_top)
        text_file.close()

        # dispatch the work into task lists
        _args = ["%s/dispatch.sh" % _import4_pkg_bin, self.rrd_dir, _tasks_Q]
        _rc = subprocess.call(
            _args, shell=False, stderr=subprocess.STDOUT)
        if _rc != 0:
            raise ImportError(ExitCode.CMD_ERROR)

        log.info("rrd files dispatched to tasks")

        # polling the task files and job/.done to report progress
        # the output pattern is hardcoded in the perf_progress.sh
        _repattern = re.compile('T:(\d+) F:(\d+) C:(\d+) D:(\d+)')

        # run until _done == _tasks
        try:
            # wait Config.perf_poll seconds before each check
            _no_progress_count = 0
            _old_progress = None
            _last_fail_line = 0
            while True:
                time.sleep(Config.perf_poll)
                _progress = subprocess.check_output(["%s/perf_progress.sh" % _import4_pkg_bin])
                if _progress == _old_progress:
                    _no_progress_count += 1
                    log.warning('No progress for %d seconds', (_no_progress_count*Config.perf_poll))
                    self.reportHeartbeat()
                    # if the progress stuck and timeout, we abort the perf import
                    if _no_progress_count > Config.perf_timeout:
                        log.error('Performance data import stalling over %d seconds, import operation aborted', (Config.perf_poll*Config.perf_timeout))
                        self.reportError('perf_import', 'Performance data import stalling, import operation aborted')
                        self.exec_cmd("%s/abort_jobs.sh" % _import4_pkg_bin)
                        raise ImportError(ExitCode.FAILURE)
                    continue
                _no_progress_count = 0
                _num = _repattern.search(_progress)
                if _num:
                    log.info(_progress.strip())
                    _tno = int(_num.group(1))
                    _fno = int(_num.group(2))
                    _cno = int(_num.group(3))
                    _dno = int(_num.group(4))
                    # _cents = int(_num.group(5))
                    # output status in json
                    if _fno > 0:
                        _now_fail_line = sum(1 for line in open(Config.perf_fail_records))
                        if _now_fail_line > _last_fail_line:
                            self.reportWarning('perf_import', 'performance data errors reported:')
                            _fail_lines = subprocess.check_output("/usr/bin/sed -n '%d,$p' %s" % (_last_fail_line+1, Config.perf_fail_records),
                                                                  shell=True)
                            for _fail_line in _fail_lines.split('\n'):
                                if _fail_line.strip():
                                    self.reportWarning('perf_import', _fail_line)
                            _last_fail_line = _now_fail_line

                    self.reportStatus(Imp4Meta.num_perfrrd, _cno)
                    self.reportStatus(Imp4Meta.num_perftsdb, _dno)

                    if (_dno >= _tno) and (_cno >= _tno):
                        break
                else:
                    # cannot recognize the progress output string
                    log.error("perf_progress.sh error:%s", _progress)
                    self.reportError('perf_import', 'Incorrect performance progress report')
                    raise ImportError(ExitCode.CMD_ERROR)
                _old_progress = _progress
        except:
            print sys.exc_info()[0]
            raise ImportError(ExitCode.FAILURE)

        with open(self.data_migrated, 'a'):
            pass

        log.info("Performance data import complete!")
        return
