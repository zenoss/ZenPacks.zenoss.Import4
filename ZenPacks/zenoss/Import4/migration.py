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
import tempfile


class Results(object):
    SUCCESS = 'SUCCESS'
    WARNING = 'WARNING'
    FAILURE = 'FAILURE'


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
    zepSocket =     '/var/lib/mysql/mysql.sock'
    zodbSocket =    '/var/lib/mysql.model/mysql.sock'


class ImportError(Exception):
    def __init__(self, error_string, return_code):
        self.return_code = return_code
        self.error_string = error_string


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
        self.log = logging.getLogger("Imp4")
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
        if args.log_level:
            logging.basicConfig(level=getattr(logging, args.log_level.upper()))
        
        if args.pname != 'import':
            self.importFunc = None
        else:
            self.importFunc = filter(None, [func for func in self.importFuncs.keys() if getattr(args, func, False)])
            self.importFunc = self.importFunc[0] if self.importFunc else 'doImport' # fall back to general import method
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
        self.log.warning("-- %s:%s:%s not implemented! --"
                         % (inspect.getmodule(caller[0]).__name__, self.__class__.__name__, caller[3]))
        # raise NotImplementedError
        return

    def prevalidate(self):
        self.__NOT_YET__()
        logging.warning("-- To be overriden!")
        return

    def wipe(self):
        self.__NOT_YET__()
        logging.warning("-- To be overriden!")
        return

    def doImport(self):
        self.__NOT_YET__()
        self.log.warning("-- To be overriden!")
        return

    def reportProgress(self, progress):
        # callback to self.progress if register at creation
        progress = progress.rstrip("\n\r\t ").lstrip("\n\r")
        self.log.debug(progress)
        if self.progress:
            self.progress(progress + "\n")

    def postvalidate(self):
        self.__NOT_YET__()
        self.log.warning("-- To be overriden!")
        return

    def startZenoss(self):
        # now bring back zenoss processes AFTER the new zope image is committed
        self.reportProgress('Restarting zenoss services...')
        _cmd = '%s/imp4util.py --log-level=%s start_all_svcs' % (self.binpath, self.args.log_level)
        self.log.debug('-> %s' % _cmd)
        self.exec_cmd(_cmd)
        return

    '''
    Utility methods
    '''
    # execute a command and pocesses the stdout/stderr
    def exec_cmd(self, cmd):
        # prep for the error log file for the restoration command
        _errfile = tempfile.NamedTemporaryFile(
            mode='w+b', dir=self.tempDir, prefix='_zen', delete=False)

        self.log.debug('Executing %s ...' % cmd)

        proc = subprocess.Popen(cmd, shell=True,
                                stdout=subprocess.PIPE, stderr=_errfile)
        # report the execution status
        while True:
            _line = proc.stdout.readline()
            if _line:
                _line.strip()
                self.reportProgress(_line)
            else:
                break
        proc.wait()

        if proc.returncode != 0:
            # report the stderr of the subprocess
            # only if the return code is not success
            _errfile.seek(0)
            while True:
                raw_line = _errfile.readline().rstrip()
                if raw_line != '':
                    self.reportProgress("[STDERR]" + raw_line)
                else:
                    break
            _errfile.close()
            self.reportProgress(Results.FAILURE)
            raise ImportError(Results.FAILURE, proc.returncode)

        _errfile.close()
        return

    # socket must be supplied because
    # we use two different sockets for zep and zodb
    def restoreMySqlDb(self, sql_path, db, socket):
        """
        Create MySQL database if it doesn't exist.
        """
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
            raise ImportError(Results.FAILURE, _rc)

        if sql_path.endswith('.gz'):
            cmd_fmt = "gzip -dc {sql_path}"
        else:
            cmd_fmt = "cat {sql_path}"
        cmd_fmt += " | {mysql_cmd} {db}"
        cmd = cmd_fmt.format(**locals())

        self.exec_cmd(cmd)
        return
