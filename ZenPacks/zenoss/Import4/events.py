##############################################################################
#
# Copyright (C) Zenoss, Inc. 2014-2015, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

import os
import subprocess

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


class Migration(MigrationBase):
    def __init__(self, args, progressCallback):
        # common setup setup
        super(Migration, self).__init__(args, progressCallback)
        self.zenbackup_dir = Config.zenbackupDir
        self.zep_sql = ''
        self.insert_count = 0
        self.insert_running = 0
        self.event_migrated = '%s/EVENT_MIGRATED' % self.tempDir

    @classmethod
    def init_command_parser(cls, m_parser):
        pass
        # MigrationBase.init_command_parser(m_parser)
        # add specific arguments for events migration

    def prevalidate(self):
        # untar the provided zenbackup package
        # exception from this passed upward
        if not self.zbfile:
            self.reportProgress(_stderr_tag + 'No zenbackup package provided..')
            raise EventImportError(Results.UNTAR_FAIL, -1)

        self._untarZenbackup()
        self._check_files()
        self.reportProgress(Results.SUCCESS)
        return

    def _check_files(self):
        # check the untar results
        self.reportProgress(
            _check_tag+'checking directories - "%s"..' % self.zenbackup_dir)

        if not os.path.isdir(self.zenbackup_dir):
            self.reportProgress(
                _stderr_tag + 'Backup directory does not exist. Run -c option to extract the backup file.')
            raise EventImportError(Results.INVALID, -1)
        self.reportProgress(_check_tag + 'zenbackup directory exists')

        # attempt to find the compressed zep.sql file
        self.zep_sql = '%s/%s' % (self.tempDir, Config.zepSQL)
        _gzfile = '%s/%s' % (self.tempDir, Config.zepBackup)

        # if compressed file found, uncompressed it to zep.sql
        if os.path.isfile(_gzfile):
            self.exec_cmd('gunzip %s' % _gzfile)

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
            _check_tag + 'directory "%s" for events looks OK' % self.zenbackup_dir)

        # all files in place
        return

    def wipe(self):
        # this will be done by the import itself
        self.reportProgress(_check_tag + 'Wipe is done by the import')
        return

    def doImport(self):
        if os.path.isfile(self.event_migrated):
            os.remove(self.event_migrated)

        # the check_files is fast so we always do a quick check
        self._check_files()

        # stop services accessing zodb
        # use the provided control center IP for service controls
        _util_cmd = "%s/imp4util.py" % self.binpath
        if self.args.control_center_ip:
            _util_cmd = "CONTROLPLANE_HOST_IPS=%s " % self.args.control_center_ip + _util_cmd

        # stop services accessing zenoss_zep
        self.reportProgress('Stopping services ...')
        _cmd = "%s --log-level=%s stop_svcs" % (_util_cmd, self.args.log_level)
        self.exec_cmd(_cmd)

        self._restoreMySqlDb('zenoss_zep')
        self._migrateSchema()
        with open(self.event_migrated, 'a'):
            pass

        # restart services
        self.reportProgress('Stopping services ...')
        _cmd = "%s --log-level=%s start_all_svcs" % (_util_cmd, self.args.log_level)
        self.exec_cmd(_cmd)

        self.reportProgress(Results.SUCCESS)
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
        if os.path.isfile(self.event_migrated):
            self.reportProgress(
                _check_tag + 'Previous "-x event" is successful, No post validation needed.')
            self.reportProgress(Results.SUCCESS)
        else:
            self.reportProgress(
                _check_tag + 'Previous "-x event" is not successful or not imported yet.')
            self.reportProgress(Results.FAILURE)
        return

    def _migrateSchema(self):
        _cmd = ['/opt/zenoss/bin/zeneventserver-create-db',
                '--dbtype', 'mysql',
                '--dbuser', "'%s'" % self.user,
                '--dbpass', "'%s'" % self.password,
                '--schemadir', '/opt/zenoss/share/zeneventserver/sql',
                '--update_schema_only']
        _cmdstr = subprocess.list2cmdline(_cmd)
        _rc = subprocess.call(_cmdstr, shell=True)
        if _rc > 0:
            raise EventImportError(Results.COMMAND_ERROR, _rc)
        return

    def _untarZenbackup(self):
        """
        unpack the backup package to sql files
        """
        # remove the target dir
        if not os.path.exists(self.tempDir):
            os.makedirs(self.tempDir)
        cmd = 'cd %s; rm -f %s %s' % (self.tempDir, Config.zepBackup, Config.zepSQL)
        self.exec_cmd(cmd)
        cmd = 'tar --wildcards-match-slash -C %s -f %s -x %s' % (
            self.tempDir, self.zbfile.name, Config.zepBackup)
        self.exec_cmd(cmd)
        return
