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
import shutil
from distutils.dir_util import copy_tree

from ZenPacks.zenoss.Import4.migration import MigrationBase, ImportError, Config, ExitCode, codeString, log

# some common tags
_check_tag = '[Check] '
_stderr_tag = '[STDERR] '
_import_prefix = 'Event: '


class Migration(MigrationBase):

    importFuncs = {
        'database': {
            'desc': 'Import the events database'
        },
        'index': {
            'desc': 'Import the zeneventserver index'
        }
    }

    def __init__(self, args, progressCallback):
        # common setup setup
        super(Migration, self).__init__(args, progressCallback)
        self.zep_sql = ''
        self.insert_count = 0
        self.insert_running = 0
        self.index_dir = ''

    @staticmethod
    def init_command_parser(m_parser):
        pass

    @classmethod
    def init_command_parsers(cls, check_parser, verify_parser, import_parser):
        super(Migration, cls).init_command_parsers(check_parser, verify_parser, import_parser)

    def prevalidate(self):
        self._check_files()
        self.reportProgress(codeString[ExitCode.SUCCESS])
        return

    def _check_files(self):
        # check the untar results
        self.reportProgress(
            _check_tag+'checking directories - "%s"..' % self.zenbackup_dir)

        if not os.path.isdir(self.zenbackup_dir):
            self.reportProgress(
                _stderr_tag + 'Backup directory does not exist. Run `events check` command to extract the backup file.')
            raise ImportError(ExitCode.INVALID)
        self.reportProgress(_check_tag + 'zenbackup directory exists')

        # attempt to find the compressed zep.sql file
        self.zep_sql = '%s/%s' % (self.zenbackup_dir, Config.zepSQL)
        _gzfile = '%s/%s' % (self.zenbackup_dir, Config.zepBackup)

        # if compressed file found, uncompressed it to zep.sql
        if os.path.isfile(_gzfile):
            self.exec_cmd('gunzip %s' % _gzfile)

        if not os.path.isfile(self.zep_sql):
            raise ImportError(ExitCode.INVALID)

        # obtain the number of insert counts
        self.insert_count = int(subprocess.check_output(
            'egrep "^INSERT INTO" %s|wc -l' % self.zep_sql, shell=True))
        if self.insert_count <= 0:
            raise ImportError(ExitCode.INVALID)

        # find zep indicies
        indexDir = os.path.join(self.zenbackup_dir, Config.zepIndexDir)
        if os.path.isdir(indexDir):
            self.index_dir = indexDir
            log.info("Found zeneventserver index dir %s", self.index_dir)
        else:
            log.info("No zeneventserver indexes found")

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

    #==========================================================================
    # Import methods
    #==========================================================================
    def database(self):
        self._check_files()
        self.restoreMySqlDb(self.zep_sql, 'zenoss_zep', Config.zepSocket)
        self._migrateSchema()
        self.reportProgress(codeString[ExitCode.SUCCESS])
        return

    def index(self):
        self._check_files()
        # Always remove this, even if there's no new one
        zep_index = "/opt/zenoss/var/zeneventserver/index"
        shutil.rmtree(zep_index, ignore_errors=True)
        self.reportProgress("Successfully removed existing zeneventserver indexes")
        if self.index_dir:
            copy_tree(self.index_dir, zep_index)
            self.reportProgress("Successfully copied zeneventserver indexes from backup to {}".format(zep_index))
        else:
            self.reportProgress("Zeneventserver index backup not found, so skipping restore")

        self.reportProgress(codeString[ExitCode.SUCCESS])
        return

    #==========================================================================

    def reportProgress(self, raw_line):
        # filtering the lines
        _msg = ''
        if raw_line.find(_check_tag) == 0 or \
                raw_line.find(_stderr_tag) == 0 or \
                raw_line.find('LOCK TABLES') == 0 or \
                raw_line.find('DROP TABLE') == 0 or \
                raw_line.find(codeString[ExitCode.SUCCESS]) == 0:
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
                _check_tag + 'Previous "event import" is successful, No post validation needed.')
            self.reportProgress(codeString[ExitCode.SUCCESS])
        else:
            self.reportProgress(
                _check_tag + 'Previous "event import" is not successful or not imported yet.')
            self.reportProgress(codeString[ExitCode.FAILURE])
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
            raise ImportError(ExitCode.COMMAND_ERROR, _rc)
        return
