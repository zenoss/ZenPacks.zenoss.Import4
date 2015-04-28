##############################################################################
#
# Copyright (C) Zenoss, Inc. 2014-2015, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

'''
Import the models backed up in the zenbackup tarball
'''

import os
import sys
import subprocess

from ZenPacks.zenoss.Import4.migration import MigrationBase, ImportError, Config


class Results(object):
    COMMAND_ERROR = 'MODELMIGRATION_COMMAND_ERROR'
    UNTAR_FAIL = 'MODELMIGRATION_UNTAR_FAILED'
    INVALID = 'MODELMIGRATION_INVALID'
    WARNING = 'MODELMIGRATION_WARNING'
    FAILURE = 'MODELMIGRATION_FAILURE'
    SUCCESS = 'MODELMIGRATION_SUCCESS'


class ModelImportError(ImportError):
    def __init__(self, error_string, return_code):
        super(ModelImportError, self).__init__(error_string, return_code)

class Migration(MigrationBase):
    def __init__(self, args, progressCallback):
        super(Migration, self).__init__(args, progressCallback)
        # all the args is in self.args
        self.zenbackup_dir = Config.zenbackupDir
        self.zodb_sql = ''
        self.zenpack_count = 0
        self.insert_count = 0
        self.insert_running = 0
        self.model_migrated = '%s/MODEL_MIGRATED' % self.tempDir

    @classmethod
    def init_command_parser(cls, m_parser):
        pass

    def prevalidate(self):
        if not self.zbfile:
            self.log.warning('No zenbackup package provided..')
            self.reportProgress('No zenbackup package provided..')
            raise ModelImportError(Results.UNTAR_FAIL, -1)

        self._untarBackup()
        self._check_files()
        self.reportProgress('...Success...')
        return

    def reportProgress(self, raw_line):
        # process output lines if it contains certain pattern
        self.log.debug(raw_line)
        _msg =  raw_line
        if (_msg.find('STDERR') == 0 or
            _msg.find('LOCK TABLES') == 0 or
            _msg.find('DROP TABLE') == 0 or
            _msg.find('INSERT INTO ') == 0 or
            _msg.find('CREATE TABLE') == 0):
            _msg = _msg.split('(', 1)[0]
        if len(_msg) > 255:
            _msg = _msg[:255]
        super(Migration, self).reportProgress(_msg)

    def wipe(self):
        self.reportProgress('Wipe is done while importing zodb')

    def doImport(self):
        if os.path.isfile(self.model_migrated):
            os.remove(self.model_migrated)

        self._check_files()

        # stop services accessing zodb
        self.reportProgress('Stopping services ...')
        _cmd = "%s/imp4util.py --log-level=%s stop_svcs" % (self.binpath, self.args.log_level)
        self.exec_cmd(_cmd)

        # restore zodb
        self.reportProgress('Restoring zodb ...')
        self.restoreMySqlDb(self.zodb_sql, 'zodb', Config.zodbSocket)

        # fix schema if needed
        # self.reportProgress('No ZODB schema changes ...')

        # zip up the zenpacks in the backup ZenPack dir
        # copy it to /opt/zenoss/.ZenPack
        self.reportProgress('Create and copying the 4.x zenpacks eggs ...')
        _cmd = "%s/get_eggs.sh" % self.binpath
        self.exec_cmd(_cmd)

        # bring back zep, zcs, rabbit redis services
        self.reportProgress('Restaring necessary services for model import...')
        _cmd = "%s/imp4util.py --log-level=%s start_model_svcs" % (
            self.binpath, self.args.log_level)
        self.exec_cmd(_cmd)

        # dmd del black list zenpacks (commit)
        self.reportProgress('Removing the non 5.x compatible zenpacks from zodb ...')
        _cmd = "zendmd --script=%s/del_dmdobjs.dmd --commit" % self.binpath
        self.exec_cmd(_cmd)

        # zenpack --restore AND --ignore-services and --keep-pack
        self.reportProgress('Fixing zenpack in zodb and files on the image ...')
        _cmd = "zenpack --restore --keep-pack=ZenPacks.zenoss.Import4"
        self.exec_cmd(_cmd)

        # zencatalog
        self.reportProgress('Recatalog zodb ...')
        _cmd = "%s/recat.sh" % self.binpath
        self.exec_cmd(_cmd)

        # mark migration done
        with open(self.model_migrated, 'a'):
            pass

        self.reportProgress(Results.SUCCESS)
        # commit image is done by the run command from serviced

        return

    def postvalidate(self):
        self.__NOT_YET__()

    def _untarBackup(self):
        '''
        unpack the backup package
        '''
        if not os.path.exists(self.tempDir):
            os.makedirs(self.tempDir)

        self.exec_cmd('/usr/bin/rm -f %s/%s %s/%s' % (self.tempDir, Config.zodbBackup,
                                                      self.tempDir, Config.zodbSQL))
        self.exec_cmd('/usr/bin/rm -rf %s/%s' % (self.tempDir, Config.zenpackDir))

        # get zodb.sql.gz and ZenPacks.tar
        cmd = 'tar --wildcards-match-slash -C %s -f %s -x %s -x %s' % (
            self.tempDir, self.zbfile.name, Config.zodbBackup, Config.zenpackBackup)
        self.log.debug(cmd)
        self.exec_cmd(cmd)

        # get the ZenPacks dir from ZenPacks.tar
        cmd = 'tar --wildcards-match-slash -C %s -xf %s/%s' % (
            self.tempDir, self.tempDir, Config.zenpackBackup)
        self.log.debug(cmd)
        self.exec_cmd(cmd)

        return

    def _check_files(self):
        self.reportProgress('checking directories ...')

        if not os.path.isdir(self.zenbackup_dir):
            self.log.error('Backup directory does not exist. Run -c option to extract the backupfiles.')
            raise ModelImportError(Results.INVALID, -1)

        self.zodb_sql = '%s/%s' % (self.tempDir, Config.zodbSQL)
        _gzfile = '%s/%s' % (self.tempDir, Config.zodbBackup)

        if os.path.isfile(_gzfile):
            _rc = os.system('gunzip %s' % _gzfile)
            if _rc > 0:
                self.log.error('Failed to unzip %s' % _gzfile)
                raise ModelImportError(Results.INVALID, -1)

        if not os.path.isfile(self.zodb_sql):
                raise ModelImportError(Results.INVALID, -1)

        self.insert_count = int(subprocess.check_output(
            'egrep "^INSERT INTO" %s | wc -l' % self.zodb_sql, shell=True))
        if self.insert_count <= 0:
            self.log.error("Cannot find any INSERT statement in %s" % self.zodb_sql)
            raise ModelImportError(Results.INVALID, -1)

        self.reportProgress('%s file is OK' % self.zodb_sql)
        self.reportProgress('A rough scan shows [%d] INSERT statements'
                            % self.insert_count)

        # check egg directories
        self.zenpack_count = int(subprocess.check_output(
            'find %s/ZenPacks -type d -name "*.egg" | wc -l' % self.tempDir, shell=True))
        if self.zenpack_count <= 0:
            self.log.error("No zenpack found in %s/ZenPacks!" % self.tempDir)
            raise ModelImportError(Results.INVALID, -1)
        self.reportProgress('%d zenpack directories in "%s/ZenPacks"' % (self.zenpack_count, self.tempDir))

        self.reportProgress('directory "%s" for models looks OK' % self.zenbackup_dir)
        return
