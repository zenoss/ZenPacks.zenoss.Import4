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
import subprocess
import logging

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


def init_command_parser(subparsers):
    model_parser = subparsers.add_parser('model', help='migrate model data')
    return model_parser


class Migration(MigrationBase):
    def __init__(self, args, progressCallback):
        super(Migration, self).__init__(args, progressCallback)
        # all the args is in self.args
        self.zenbackup_dir = Config.zenbackupDir
        self.zodb_sql = ''
        self.zenpack_count = 0
        self.insert_count = 0
        self.insert_running = 0
        self.model_mirated = '%s/MODEL_MIGRATED' % self.tempDir

    def prevalidate(self):
        if not self.zbfile:
            logging.warning('No zenbackup package provided..')
            self.reportProgress('No zenbackup package provided..')
            raise ModelImportError(Results.UNTAR_FAIL, -1)

        self._untarBackup()
        self._checkFiles()
        self.reportProgress('...Success...')
        return

    def reportProgress(self, raw_line):
        super(Migration, self).reportProgress(raw_line)

    def wipe(self):
        self.__NOT_YET__()

    def doImport(self):
        self.__NOT_YET__()

    def postvalidate(self):
        self.__NOT_YET__()

    def _untarBackup(self):
        '''
        unpack the backup backage
        '''
        if not os.path.exists(self.tempDir):
            os.makedirs(self.tempDir)
        cmd = 'cd %s; rm -f %s %s' % (self.tempDir, Config.zodbBackup, Config.zodbSQL)
        _rc = os.system(cmd)
        if _rc > 0:
            raise ModelImportError(Results.COMMAND_ERROR, _rc)

        # get zodb.sql.gz and ZenPacks.tar
        cmd = 'tar --wildcards-match-slash -C %s -f %s -x %s -x %s' % (
            self.tempDir, self.zbfile.name, Config.zodbBackup, Config.zenpackBackup)
        logging.debug(cmd)
        _rc = os.system(cmd)
        if _rc:
            logging.error("Fail to get %s or %s", Config.zodbBackup, Config.zenpackBackup)
            raise ModelImportError(Results.UNTAR_FAIL, _rc)

        # get the ZenPacks dir from ZenPacks.tar
        cmd = 'tar --wildcards-match-slash -C %s -xf %s/%s' % (
            self.tempDir, self.tempDir, Config.zenpackBackup)
        logging.debug(cmd)
        _rc = os.system(cmd)
        if _rc:
            logging.error("Fail to extract ZenPacks directory in %s" % Config.zenpackBackup)
            raise ModelImportError(Results.UNTAR_FAIL, _rc)

        return

    def _checkFiles(self):
        self.reportProgress('checking directories ...')

        if not os.path.isdir(self.zenbackup_dir):
            logging.error('Backup directory does not exist. Run -c option to extract the backupfiles.')
            raise ModelImportError(Result.INVALID, -1)

        self.zodb_sql = '%s/%s' % (self.tempDir, Config.zodbSQL)
        _gzfile = '%s/%s' % (self.tempDir, Config.zodbBackup)

        if os.path.isfile(_gzfile):
            _rc = os.system('gunzip %s' % _gzfile)
            if _rc > 0:
                logging.error("Fail to unzip %s" % _gzfile)
                raise ModelImportError(Results.INVALID, -1)

        if not os.path.isfile(self.zodb_sql):
                raise ModelImportError(Results.INVALID, -1)

        self.insert_count = int(subprocess.check_output(
            'egrep "^INSERT INTO" %s|wc -l' % self.zodb_sql, shell=True))
        if self.insert_count <= 0:
            logging.error("Cannot find any INSERT statement in %s" % self.zodb_sql)
            raise ModelImportError(Results.INVALID, -1)

        self.reportProgress('%s file is OK' % self.zodb_sql)
        self.reportProgress('A rough scan shows [%d] INSERT statements'
                            % self.insert_count)

        # check egg directories
        self.zenpack_count = int(subprocess.check_output(
            'find %s/ZenPacks -type d -name "*.egg" | wc -l' % self.tempDir, shell=True))
        if self.zenpack_count <= 0:
            logging.error("No zenpack found in %s/ZenPacks!" % self.tempDir)
            raise ModelImportError(Results.INVALID, -1)
        self.reportProgress('%d zenpack directories in "%s/ZenPacks"' % (self.zenpack_count, self.tempDir))

        self.reportProgress('directory "%s" for models looks OK' % self.zenbackup_dir)
        return
