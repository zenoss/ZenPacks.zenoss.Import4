##############################################################################
#
# Copyright (C) Zenoss, Inc. 2014-2015, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

import argparse
import os
import subprocess
import tempfile

from ZenPacks.zenoss.Import4.migration import MigrationBase, ImportError, Config

# some common tags
_check_tag = '[Check] '
_stderr_tag = '[STDERR] '
_import_prefix = 'Event: '


class Results(object):
    COMMAND_ERROR = 'EVENTMIGRATION_COMMAND_ERROR'
    UNTAR_FAIL = 'EVENTMIGRATION_UNTAR_FAILED'
    INVALID = 'EVENTMIGRATION_INVALID'
    WARNING = 'EVENTMIGRATION_WARNING'
    FAILURE = 'EVENTMIGRATION_FAILURE'
    SUCCESS = 'EVENTMIGRATION_SUCCESS'


class EventImportError(ImportError):
    def __init__(self, error_string, return_code):
        super(EventImportError, self).__init__(error_string, return_code)


def init_command_parser(subparsers):
    # add specific arguments for events migration
    events_parser = subparsers.add_parser('event', help='migrate event data')
    return events_parser


class Migration(MigrationBase):
    def __init__(self, args, progressCallback):
        # common setup setup
        super(Migration, self).__init__(args, progressCallback)
        self.zenbackup_dir = Config.zenbackupDir
        self.zep_sql = ''
        self.insert_count = 0
        self.insert_running = 0

    def prevalidate(self):
        # untar the provided zenbackup package
        # exception from this passed upward
        if not self.zbfile:
            self.reportProgress(_stderr_tag + 'No zenbackup package provided..')
            raise EventImportError(Results.UNTAR_FAIL, -1)

        self._untarZenbackup()
        self._check_files()

    def _check_files(self):
        # check the untar results
        self.reportProgress(
            _check_tag+'checking package "%s"..' % self.zbfile.name)

        if not os.path.isdir(self.zenbackup_dir):
            raise EventImportError(Results.INVALID, -1)
        self.reportProgress(_check_tag + 'zenbackup directory found')

        # attempt to find the compressed zep.sql file
        self.zep_sql = '%s/%s' % (self.tempDir, Config.zepSQL)
        _gzfile = '%s/%s' % (self.tempDir, Config.zepBackup)

        # if compressed file found, uncompressed it to zep.sql
        if os.path.isfile(_gzfile):
            _rc = os.system('gunzip %s' % _gzfile)
            if _rc > 0:
                raise EventImportError(Results.COMMAND_ERROR, _rc)

        print self.tempDir, self.zep_sql
        if not os.path.isfile(self.zep_sql):
            raise EventImportError(Results.INVALID, -1)

        # obtain the number of insert counts
        self.insert_count = int(subprocess.check_output(
            'egrep "^INSERT INTO" %s|wc -l' % self.zep_sql, shell=True))
        if self.insert_count <= 0:
            raise EventImportError(Results.INVALID, -1)

        self.reportProgress(_check_tag + '%s file is OK' % self.zep_sql)
        self.reportProgress(_check_tag +
                            'A rough scan shows [%d] INSERT statements'
                            % self.insert_count)
        self.reportProgress(
            _check_tag + 'package "%s" looks OK' % self.zbfile.name)

        # all files in place
        return

    def wipe(self):
        # this will be done by the import itself
        self.reportProgress(_check_tag + 'Wipe is done by the import')
        return

    def doImport(self):
        self._check_files()
        self._restoreMySqlDb('zenoss_zep')
        return

    def reportProgress(self, raw_line):
        # filtering the lines
        _msg = ''
        if raw_line.find(_check_tag) == 0 or \
                raw_line.find(_stderr_tag) == 0 or \
                raw_line.find('LOCK TABLES') == 0 or \
                raw_line.find('DROP TABLE') == 0 or \
                raw_line.find(Results.SUCCESS) == 0:
            _msg = raw_line
        elif raw_line.find('CREATE TABLE') == 0:
            _msg = raw_line.split('(', 1)[0]
        elif raw_line.find('INSERT INTO ') == 0:
            self.insert_running += 1
            _msg = raw_line.split('(', 1)[0] +\
                '[%3.1f%%]' % (self.insert_running * 100.0 / self.insert_count)
        else:
            # throw away the rest
            _msg = None

        if _msg:
            _msg = _import_prefix + '%s\n' % _msg.strip()
            super(Migration, self).reportProgress(_msg)

    def postvalidate(self):
        # we assume the db operations are all correct if no error returned
        self.reportProgress(
            _check_tag + 'If previous "-x event" is successful, No post validation needed.')
        return

    def _untarZenbackup(self):
        """
        unpack the backup package to sql files
        """
        # remove the target dir
        if not os.path.exists(self.tempDir):
            os.makedirs(self.tempDir)
        cmd = 'cd %s; rm -f %s %s' % (self.tempDir, Config.zepBackup, Config.zepSQL)
        _rc = os.system(cmd)
        if _rc > 0:
            raise EventImportError(Results.COMMAND_ERROR, _rc)
        cmd = 'tar --wildcards-match-slash -C %s -f %s -x %s' % (
            self.tempDir, self.zbfile.name, Config.zepBackup)
        _rc = os.system(cmd)
        if _rc:
            raise EventImportError(Results.UNTAR_FAIL, _rc)
        return

    def _restoreMySqlDb(self, db):
        """
        Create MySQL database if it doesn't exist.
        """
        mysql_cmd = ['mysql', '-u%s' % self.user]
        mysql_cmd.extend(['--verbose'])
        if self.password:
            mysql_cmd.extend(['--password=%s' % self.password])

        if self.ip and self.ip != 'localhost':
            mysql_cmd.extend(['--host', self.ip])

        mysql_cmd = subprocess.list2cmdline(mysql_cmd)

        cmd = 'echo "create database if not exists %s" | %s' % (db, mysql_cmd)
        _rc = os.system(cmd)
        if _rc:
            raise EventImportError(Results.COMMAND_ERROR, _rc)

        sql_path = self.zep_sql
        if sql_path.endswith('.gz'):
            cmd_fmt = "gzip -dc {sql_path}"
        else:
            cmd_fmt = "cat {sql_path}"
        cmd_fmt += " | {mysql_cmd} {db}"
        cmd = cmd_fmt.format(**locals())

        # prep for the error log file for the restoration command
        _errfile = tempfile.NamedTemporaryFile(
            mode='w+b', dir=self.tempDir, prefix='_zen', delete=True)
        proc = subprocess.Popen(cmd, shell=True,
                                stdout=subprocess.PIPE, stderr=_errfile)
        while True:
            raw_line = proc.stdout.readline()
            if raw_line != '':
                self.reportProgress(raw_line)
            else:
                break

        proc.wait()
        if proc.returncode != 0:
            # report the stderr of the subprocess
            # only if the return code is not success
            _errfile.seek(0)
            while True:
                raw_line = _errfile.readline()
                if raw_line != '':
                    self.reportProgress(_stderr_tag+raw_line)
                else:
                    break
            _errfile.close()
            self.reportProgress(Results.FAILURE)
            raise EventImportError(Results.FAILURE, proc.returncode)

        _errfile.close()
        self.reportProgress(Results.SUCCESS)
        return
