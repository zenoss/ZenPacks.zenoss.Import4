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

    importFuncs = {
            'database': {
                'desc': 'Import zodb',
            },
            'catalog': {
                'desc': 'Import the global catalog',
            },
            'zenmigrate': {
                'desc': 'Run zenmigrate',
            },
            'zenpack': {
                'desc' : 'Run zenpack --restore',
            }
    }

    def __init__(self, args, progressCallback):
        super(Migration, self).__init__(args, progressCallback)
        # all the args is in self.args
        self.zodb_sql = ''
        self.zenpack_count = 0
        self.insert_count = 0
        self.insert_running = 0
        self.model_checked = '%s/MODEL_CHECKED' % self.tempDir

    @staticmethod
    def init_command_parser(m_parser):
        pass

    @classmethod
    def init_command_parsers(cls, check_parser, verify_parser, import_parser):
        super(Migration, cls).init_command_parsers(check_parser, verify_parser, import_parser)

    def prevalidate(self):
        self._check_files()

        # mark the checked file
        with open(self.model_checked, 'a'):
            pass
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

    # TOTO: Make this a decorator
    def _ready_to_import(self):
        if not os.path.exists(self.model_checked):
            self.reportProgress("Model backup file not validated yet. Run -c option first.")
            raise ModelImportError(Results.INVALID, -1)

        self._check_files()

    #==========================================================================
    # Import methods
    #==========================================================================

    def database(self):
        self._ready_to_import()
        # restore zodb
        self.reportProgress('Restoring zodb ...')
        self.restoreMySqlDb(self.zodb_sql, 'zodb', Config.zodbSocket)

        # dmd del black list zenpacks (commit)
        self.reportProgress('Removing the non 5.x compatible zenpacks from zodb ...')
        _cmd = "zendmd --script=%s/del_dmdobjs.dmd --commit" % self.binpath
        self.exec_cmd(_cmd)

        self.reportProgress('Obtain and Cache dmd uuid...')
        _cmd = "%s/set_dmduuid.sh" % self.binpath
        self.exec_cmd(_cmd)

        self.reportProgress(Results.SUCCESS)
        return

    def catalog(self):
        self._ready_to_import()
        # TODO: Actually do this.

        self.reportProgress(Results.SUCCESS)
        return

    def zenmigrate(self):
        self._ready_to_import()
        self.reportProgress('Running zenmigrate')
        _cmd = "zenmigrate"
        self.exec_cmd(_cmd)

        self.reportProgress(Results.SUCCESS)
        return

    def zenpack(self):
        self._ready_to_import()
        # zip up the zenpacks in the backup ZenPack dir
        # copy it to /opt/zenoss/.ZenPack
        self.reportProgress('Create and copying the 4.x zenpacks eggs ...')
        _cmd = '%s/get_eggs.sh "%s/ZenPacks"' % (self.binpath, self.zenbackup_dir)
        self.exec_cmd(_cmd)
        # zenpack --restore AND --ignore-services and --keep-pack
        self.reportProgress('Fixing zenpack in zodb and files on the image ...')
        _cmd = "zenpack --restore --keep-pack=ZenPacks.zenoss.Import4"
        self.exec_cmd(_cmd)

        self.reportProgress(Results.SUCCESS)
        return

    #==========================================================================

    def postvalidate(self):
        self.__NOT_YET__()

    def _check_files(self):
        self.reportProgress('checking directories ...')

        if not os.path.isdir(self.zenbackup_dir):
            self.log.error('Backup directory does not exist. Must be extracted first.')
            raise ModelImportError(Results.INVALID, -1)

        self.zodb_sql = '%s/%s' % (self.zenbackup_dir, Config.zodbSQL)
        _gzfile = '%s/%s' % (self.zenbackup_dir, Config.zodbBackup)

        if os.path.isfile(_gzfile):
            _rc = os.system('gunzip %s' % _gzfile)
            if _rc > 0:
                self.log.error('Failed to unzip %s' % _gzfile)
                raise ModelImportError(Results.INVALID, -1)

        if not os.path.isfile(self.zodb_sql):
                self.log.error('Failed to find %s' % self.zodb_sql)
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
            'find %s/ZenPacks -type d -name "*.egg" | wc -l' % self.zenbackup_dir, shell=True))
        if self.zenpack_count <= 0:
            self.log.error("No zenpack found in %s/ZenPacks!" % self.zenbackup_dir)
            raise ModelImportError(Results.INVALID, -1)
        self.reportProgress('%d zenpack directories in "%s/ZenPacks"' % (self.zenpack_count, self.zenbackup_dir))

        self.reportProgress('directory "%s" for models looks OK' % self.zenbackup_dir)
        return
