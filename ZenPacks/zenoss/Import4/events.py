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

from ZenPacks.zenoss.Import4.migration import MigrationBase, ImportError, Config, ExitCode, codeString, log, Imp4Meta


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
        self.reportMetaData(Imp4Meta.num_events, 0, self.insert_count)
        return

    def _check_files(self):
        # check the untar results
        log.info('checking directories - "%s"..', self.zenbackup_dir)

        if not os.path.isdir(self.zenbackup_dir):
            log.error('Backup directory does not exist. Run `check` command to extract the backup file.')
            raise ImportError(ExitCode.INVALID)

        log.info('zenbackup directory exists')

        # attempt to find the compressed zep.sql file
        self.zep_sql = '%s/%s' % (self.zenbackup_dir, Config.zepSQL)
        _gzfile = '%s/%s' % (self.zenbackup_dir, Config.zepBackup)

        # if compressed file found, uncompressed it to zep.sql
        if os.path.isfile(_gzfile):
            self.exec_cmd('gunzip %s' % _gzfile)

        if not os.path.isfile(self.zep_sql):
            log.error('Cannot fine input zep db file:%s', self.zep_sql)
            raise ImportError(ExitCode.INVALID)

        # obtain the number of insert counts
        self.insert_count = int(subprocess.check_output(
            'egrep "^INSERT INTO" %s|wc -l' % self.zep_sql, shell=True))
        if self.insert_count <= 0:
            log.warning('No INSERT statements in the db file:%s', self.zep_sql)
            raise ImportError(ExitCode.INVALID)

        # find zep indicies
        indexDir = os.path.join(self.zenbackup_dir, Config.zepIndexDir)
        if os.path.isdir(indexDir):
            self.index_dir = indexDir
            log.info("Found zeneventserver index dir %s", self.index_dir)
        else:
            log.info("No zeneventserver indexes found")

        log.info('%s file is OK', self.zep_sql)
        log.info('A rough scan shows [%d] INSERT statements', self.insert_count)
        log.info('directory "%s" for events looks OK', self.zenbackup_dir)

        # all files in place
        return

    def wipe(self):
        # this will be done by the import itself
        log.info('Wipe is done by the import')
        return

    #==========================================================================
    # Import methods
    #==========================================================================
    def database(self):
        self._check_files()
        self.restoreMySqlDb(self.zep_sql, 'zenoss_zep', Config.zepSocket, status_key=Imp4Meta.num_events)
        self._migrateSchema()
        log.info(codeString[ExitCode.SUCCESS])
        return

    def index(self):
        self._check_files()
        # Always remove this, even if there's no new one
        zep_index = "/opt/zenoss/var/zeneventserver/index"
        shutil.rmtree(zep_index, ignore_errors=True)
        log.info("Successfully removed existing zeneventserver indexes")
        if self.index_dir:
            copy_tree(self.index_dir, zep_index)
            log.info("Successfully copied zeneventserver indexes from backup to {}".format(zep_index))
        else:
            log.info("Zeneventserver index backup not found, so skipping restore")

        log.info(codeString[ExitCode.SUCCESS])
        return

    #==========================================================================

    def postvalidate(self):
        # we assume the db operations are all correct if no error returned
        if os.path.isfile(self.event_migrated):
            log.info('Previous "event import" is successful, No post validation needed.')
            log.info(codeString[ExitCode.SUCCESS])
        else:
            log.error('Previous "event import" is not successful or not imported yet.')
            log.error(codeString[ExitCode.FAILURE])
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
