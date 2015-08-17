##############################################################################
#
# Copyright (C) Zenoss, Inc. 2014-2015, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

import os
import inspect
import logging
import subprocess
import re

log = logging.getLogger(__name__)

#
# json output format
#
# scale meta:
# { "scale_name" : { "min" : int, "max" : int} }
# scale status:
# { "scale_name" : { "cur" : int } }


class ExitCode(object):
    # exit code used by the migration operations
    SUCCESS =       0
    WARNING =       1
    FAILURE =       2
    INVALID =       3
    CMD_ERROR =     4
    UNTAR_ERROR =   5
    RUNTIME_ERROR = 6
    UNKNOWN =      -1


# mapping of exit codes to human readable strings
codeString = {
    ExitCode.UNKNOWN: 'Unknown error',
    ExitCode.SUCCESS: 'Success',
    ExitCode.WARNING: 'Warning',
    ExitCode.FAILURE: 'Failure',
    ExitCode.INVALID: 'Invalid',
    ExitCode.CMD_ERROR: 'System command executation error',
    ExitCode.UNTAR_ERROR: 'Untar error',
    ExitCode.RUNTIME_ERROR: 'Runtime error'
}


class Imp4Meta(object):
    imp4_meta =     "imp4_meta"
    imp4_status =   "imp4_status"
    num_perf =      "numPerfChecked"
    num_perfrrd =   "RRDSourcesConversion"
    num_perftsdb =  "TSDBSourcesImport"
    num_models =    "numModelInserts"
    num_events =    "numEventInserts"
    num_zenpacks =  "numZenPacks"
    name_zenpacks = "zenpackNames"


class Config(object):
    volume =        '/import4'
    pkgPath =       '/import4/pkg'
    pkgBinPath =    '/import4/pkg/bin'
    # place of the default input data files
    mntPwdDir =     '/mnt/pwd'
    stageDir =      '/import4/staging'
    # content of a 4.x zenbackup file
    backupDir =         'zenbackup'
    catalogSvcDir =     'zencatalogservice/global_catalog/index'
    zepIndexDir =       'zeneventserver/index'
    zodbBackup =        'zodb.sql.gz'
    zodbSQL =           'zodb.sql'
    zenpackBackup =     'ZenPacks.tar'
    zenpackDir =        'ZenPacks'
    zepBackup =         'zep.sql.gz'
    zepSQL =            'zep.sql'
    perfBackup =        'perf.tar'
    perfDir =           'perf'
    # other locations
    rrdTop =        '/import4/staging/zenbackup/perf/Devices'
    zepSocket =     '/var/lib/mysql.events/mysql.sock'
    zepPort =       '3306'
    zodbSocket =    '/var/lib/mysql.model/mysql.sock'
    zodbPort =      '3307'
    perf_poll =     10
    perf_timeout =  60
    perf_fail_records = '/import4/perf.fail.records'


class ImportError(Exception):
    def __init__(self, return_code):
        self.return_code = return_code
        self.error_string = codeString[return_code]


class MigrationBase(object):
    # To be used in subclasses to define specific functions used for the 'import' step.
    # It is assumed that any dependent services for a given import step are already running
    # (or not running) when you run the import step.  Said another way, the caller needs to
    # ensure that the environment is sane.
    importFuncs = {
        """
        # The name of the function you want to provide.  Will be directly given to parser.
        theFunction: {
            # Description
            'desc': 'Description'
        }
        """
    }

    def __init__(self, args, progressCallback):
        self.binpath = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))) + '/bin'
        self.args = args
        self.progress = progressCallback
        self.tempDir = Config.mntPwdDir
        self.zenbackup_dir = "%s/%s" % (self.tempDir, Config.backupDir)
        # performance directory is extracted on the staging area
        self.perf_dir = "%s/%s/%s" % (Config.stageDir, Config.backupDir, Config.perfDir)
        self.ip = args.ip
        self.user = args.user
        if args.password:
            self.password = args.password
        else:
            self.password = ''

        # setup the log level on the root logger
        if args.log_level:
            logging.getLogger().setLevel(getattr(logging, args.log_level.upper()))

        if args.pname != 'import':
            self.importFunc = None
        else:
            self.importFunc = filter(None, [func for func in self.importFuncs.keys() if getattr(args, func, False)])
            # fall back to general import method
            self.importFunc = self.importFunc[0] if self.importFunc else 'doImport'
            self.importFunc = getattr(self, self.importFunc)

    @classmethod
    def init_command_parser(cls, parser):
        # import is divided into three optional stages:
        # check, import, and validate
        parser.add_argument('-f', '--ignore-warnings', action='store_true', dest='ignorewarnings', default=False,
                            help="Continue with the import even if pre-validation generates warnings")
        parser.add_argument('-l', '--log-level', dest='log_level', default='info',
                            help="Specify the logging level - default:info")
        parser.add_argument('-i', '--ip', dest='ip', default="localhost",
                            help="The ip address for MariaDB host")
        parser.add_argument('-u', '--user', dest='user', default='root',
                            help="The username for MariaDB access")
        parser.add_argument('-p', '--password', dest='password', default=None,
                            help="The password for MariaDB access")
        parser.add_argument('--cc-ip', dest='control_center_ip', default=None,
                            help="The IP address for Control Center")

    @classmethod
    def init_command_parsers(cls, check_parser, verify_parser, import_parser):
        if cls.importFuncs:
            group = import_parser.add_mutually_exclusive_group(required=True)
            for func, details in cls.importFuncs.iteritems():
                group.add_argument('--{}'.format(func), action='store_true', help=details['desc'])

    def __NOT_YET__(self):
        caller = inspect.stack()[1]
        log.warning("-- %s:%s:%s not implemented! --"
                    % (inspect.getmodule(caller[0]).__name__, self.__class__.__name__, caller[3]))
        # raise NotImplementedError
        return

    def prevalidate(self):
        self.__NOT_YET__()
        log.warning("-- To be overriden!")
        return

    def wipe(self):
        self.__NOT_YET__()
        log.warning("-- To be overriden!")
        return

    def doImport(self):
        self.__NOT_YET__()
        log.warning("-- To be overriden!")
        return

    def reportProgress(self, progress):
        # callback to self.progress if register at creation
        progress = progress.rstrip("\n\r\t ").lstrip("\n\r")
        log.debug(progress)
        if self.progress:
            self.progress(progress + "\n")

    def postvalidate(self):
        self.__NOT_YET__()
        log.warning("-- To be overriden!")
        return

    def startZenoss(self):
        # now bring back zenoss processes AFTER the new zope image is committed
        log.info('Restarting zenoss services...')
        _cmd = '%s/imp4util.py --log-level=%s start_all_svcs' % (self.binpath, self.args.log_level)
        log.debug('-> %s' % _cmd)
        self.exec_cmd(_cmd)
        return

    '''
    Utility methods
    '''
    # execute a command and pocesses its stdout/stderr
    # all output of subcommand execution are piped to subprocess stderr.
    def exec_cmd(self, cmd, status_key=None, status_max=0, status_re=None, to_log_re='.', to_log=True):
        '''
        Using Shell to execute the provided shell command.
        Both stdout and stderr of the execution are piped to stdout.
        Each output line is matched by two regex pattern status_re and to_log_re:
            if a line matches status_re, exec_cmd calls reportStatus to output the status
            if matching to_log_re, the line is sent the current logger at info level
            if to_log_re is '.', then all output lines are logged.
        '''
        log.info('>>> %s enter ...', cmd)

        proc = subprocess.Popen(cmd, shell=True,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                bufsize=0)

        # log every output
        _status_cnt = 0
        while True:
            _line = proc.stdout.readline()
            if _line:
                if to_log and re.search(to_log_re, _line):
                    log.info('> %s', _line.rstrip())

                # process the status if requested
                if status_key and status_re:
                    match = re.search(status_re, _line)
                    if match:
                        _status_cnt += 1
                        # ignore extraneous status lines after status_max
                        if _status_cnt < status_max:
                            self.reportStatus(status_key, _status_cnt)
                        elif status_max > 0:
                            # a heart beat for progress
                            self.reportStatus(status_key, status_max-1)
                    else:
                        pass
            else:
                break
        proc.wait()
        log.info('>>> %s exit .', cmd)

        if proc.returncode != 0:
            # report the error of the subprocess
            err_msg = '[%s]:%s(%d)' % (codeString[ExitCode.CMD_ERROR], cmd, proc.returncode)
            log.error(err_msg)
            raise ImportError(ExitCode.CMD_ERROR)

        # output status_max indicating completion successfully
        if status_key:
            self.reportStatus(status_key, status_max)
        return

    def reportMetaData(self, keyname, key_min, key_max):
        """
        This method reports metadata to the caller.  External integrations
        rely on this json format not changing, all the way down to having
        just one keyname.  For example, if you want to report about 2 different
        metadatas, make 2 separate calls to this function - do not try and
        construct a keyname with multiple keys in it.
        """
        self.reportProgress('{"imp4_meta": {"%s": {"min": %d, "max": %d}}}' % (keyname, key_min, key_max))

    def reportStatus(self, keyname, key_value):
        self.reportProgress('{"imp4_status": {"%s": %d}}' % (keyname, key_value))

    def reportWarning(self, keyname, key_string):
        self.reportProgress('{"imp4_warning": {"%s": "%s"}}' % (keyname, key_string))

    def reportError(self, keyname, key_string):
        self.reportProgress('{"imp4_error": {"%s": "%s"}}' % (keyname, key_string))

    def reportHeartbeat(self):
        self.reportProgress('{"imp4_status" : {}}')

    # socket must be supplied because
    # we use two different sockets for zep and zodb
    def restoreMySqlDb(self, sql_path, db, socket, status_key='sql', status_max=0):
        """
        Create MySQL database if it doesn't exist.
        """

        # obtain the number of insert statements again
        if status_max <= 0:
            status_max = int(subprocess.check_output(
                'egrep "^INSERT INTO" %s | wc -l' % sql_path, shell=True))
            if status_max <= 0:
                log.error("Cannot find any INSERT statement in %s" % sql_path)

        mysql_cmd = ['mysql', '--socket=%s' % socket, '-u%s' % self.user]
        mysql_cmd.extend(['--verbose'])
        if self.password:
            mysql_cmd.extend(['--password=%s' % self.password])

        if self.ip and self.ip != 'localhost':
            mysql_cmd.extend(['--host', self.ip])

        mysql_cmd = subprocess.list2cmdline(mysql_cmd)

        cmd = 'echo "create database if not exists %s" | %s' % (db, mysql_cmd)
        _rc = os.system(cmd)
        if _rc:
            raise ImportError(ExitCode.FAILURE)

        # sql_path is already gunzipped by the check run command
        cmd_fmt = "cat {sql_path}"
        cmd_fmt += " | {mysql_cmd} {db}"
        cmd = cmd_fmt.format(**locals())

        # using 'INSERT INTO' as progress indicator
        self.exec_cmd(cmd, status_key=status_key, status_max=status_max, status_re='^INSERT INTO ', to_log=False)
        return
