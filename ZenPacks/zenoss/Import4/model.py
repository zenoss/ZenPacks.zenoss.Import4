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
import shutil
from distutils.dir_util import copy_tree

from ZenPacks.zenoss.Import4.migration import MigrationBase, ImportError, Config, ExitCode, codeString, Imp4Meta

import logging
log = logging.getLogger(__name__)


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
                'desc': 'Run zenpack --restore',
            }
    }

    def __init__(self, args, progressCallback):
        super(Migration, self).__init__(args, progressCallback)
        # all the args is in self.args
        self.zodb_sql = ''
        self.catalog_dir = ''
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

        self.reportMetaData(Imp4Meta.num_models, 0, self.insert_count)
        self.reportMetaData(Imp4Meta.num_zenpacks, 0, self.zenpack_count)

        # mark the checked file
        with open(self.model_checked, 'a'):
            pass
        log.info('Model files checked.')

        return

    def wipe(self):
        log.info('Wipe is done while importing zodb')

    # TOTO: Make this a decorator
    def _ready_to_import(self):
        if not os.path.exists(self.model_checked):
            log.error("Model backup file not validated yet. Run `check` command first.")
            self.reportError('model_import', 'Model backup file not validated')
            raise ImportError(ExitCode.INVALID)
        self._check_files()

    #==========================================================================
    # Import methods
    #==========================================================================

    def database(self):
        self._ready_to_import()
        # restore zodb
        log.info('Restoring zodb ...')

        # reportStatus is called by restoreMySqlDB -> exec_cmd
        self.restoreMySqlDb(self.zodb_sql, 'zodb', Config.zodbSocket, status_key=Imp4Meta.num_models)
        log.info('Zodb restored ...')

        # copy the license files for ucspm if exist
        if os.path.isdir("%s/flexera" % Config.mntPwdDir):
            log.info('License directory found, copying license files ...')
            _cmd = "%s/cp_license.sh" % self.binpath
            self.exec_cmd(_cmd)
            log.info('License files copied ...')

        log.info(codeString[ExitCode.SUCCESS])
        return

    def catalog(self):
        self._ready_to_import()
        if self.catalog_dir:
            zcs_index = "/opt/zenoss/var/zencatalogservice/global_catalog/index"
            shutil.rmtree(zcs_index, ignore_errors=True)
            log.info("Successfully removed existing global catalog index")

            copy_tree(
                    self.catalog_dir,
                    zcs_index
            )
            log.info("Successfully copied catalog from backup to {}".format(zcs_index))
        else:
            log.info("Skipping external catalog restore")

        log.info("copying catalog dir:%s", codeString[ExitCode.SUCCESS])
        return

    def zenmigrate(self):
        self._ready_to_import()
        # dmd del black list zenpacks (commit)
        dmdObjsRetries = 0
        dmdObjsException = None
        while dmdObjsRetries < 3: # ZEN-18740
            try:
                self.reportProgress('Removing the non 5.x compatible zenpacks from zodb ...')
                _cmd = "zendmd --script=%s/del_dmdobjs.dmd" % self.binpath
                self.exec_cmd(_cmd)
                break
            except ImportError as e:
                log.warning('Failed to run dmd script to remove dmd objects, will retry up to 2 times')
                dmdObjsException = e
                dmdObjsRetries += 1
        if dmdObjsRetries == 3:
            raise dmdObjsException

        # zenmigrate
        log.info('Running zenmigrate')
        _cmd = "zenmigrate"
        self.exec_cmd(_cmd)

        log.info("zenmigrate:%s", codeString[ExitCode.SUCCESS])
        return

    def zenpack(self):
        self._ready_to_import()
        # zip up the zenpacks in the backup ZenPack dir
        # copy it to /opt/zenoss/.ZenPack
        log.info('Create and copying the 4.x zenpacks eggs ...')
        _cmd = '%s/get_eggs.sh "%s/ZenPacks"' % (self.binpath, self.zenbackup_dir)
        self.exec_cmd(_cmd, to_log=False)

        # zenpack --restore AND --ignore-services and --keep-pack
        log.info('Fixing zenpack in zodb and files on the image ...')
        #_cmd = "zenpack --restore --keep-pack=ZenPacks.zenoss.Import4"
        _cmd = "%s/zenpack_restore.sh" % self.binpath
        self.exec_cmd(_cmd, status_key='numZenPacks', status_re='Successfully Installed ZenPack', status_max=self.zenpack_count)

        log.info("zenpacks restored:%s", codeString[ExitCode.SUCCESS])
        return

    #==========================================================================

    def postvalidate(self):
        log.info("validating the zenpacks and devices")
        _cmd = "zendmd --script=%s/check_model.dmd" % self.binpath
        self.exec_cmd(_cmd)

        log.info("Model restored OK")
        return

    def _check_files(self):
        log.info('checking directories ...')

        if not os.path.isdir(self.zenbackup_dir):
            log.error('Backup directory does not exist. Must be extracted first.')
            self.reportError('model_import', 'Model backup files not extracted')
            raise ImportError(ExitCode.INVALID)

        self.zodb_sql = '%s/%s' % (self.zenbackup_dir, Config.zodbSQL)
        _gzfile = '%s/%s' % (self.zenbackup_dir, Config.zodbBackup)

        if os.path.isfile(_gzfile):
            _rc = os.system('gunzip %s' % _gzfile)
            if _rc > 0:
                log.error('Failed to unzip %s', _gzfile)
                self.reportError('model_import', 'Unzip zodb backup failed')
                raise ImportError(ExitCode.INVALID)

        if not os.path.isfile(self.zodb_sql):
                log.error('Failed to find %s', self.zodb_sql)
                raise ImportError(ExitCode.INVALID)

        self.insert_count = int(subprocess.check_output(
            'egrep "^INSERT INTO" %s | wc -l' % self.zodb_sql, shell=True))
        if self.insert_count <= 0:
            log.error("Cannot find any INSERT statement in %s", self.zodb_sql)
            self.reportError('model_import', 'Invalid zodb sql file')
            raise ImportError(ExitCode.INVALID)

        log.info('%s file is OK', self.zodb_sql)
        log.info('A rough scan shows [%d] INSERT statements', self.insert_count)

        # check catalog
        catalogDir = os.path.join(self.zenbackup_dir, Config.catalogSvcDir)
        if os.path.isdir(catalogDir):
            self.catalog_dir = catalogDir
            log.info("Found catalog dir %s", self.catalog_dir)
        else:
            log.info("No external catalog backup found")

        # check eggs in zenpack_actions.txt_original
        self.zenpack_count = int(subprocess.check_output(
            "wc -l /opt/zenoss/var/zenpack_actions.txt_original | awk '{print $1;}'",
            shell=True))
        if self.zenpack_count <= 0:
            log.error("No zenpacks found in zenpack_actions.txt_original")
            self.reportError('model_import', 'No zenpacks found to install')
            raise ImportError(ExitCode.INVALID)
        log.info('%d zenpacks in "/opt/zenoss/var/zenpack_actions.txt_original"', self.zenpack_count)

        log.info('directory "%s" for models looks OK', self.zenbackup_dir)
        return
