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

    def prevalidate(self):
        if not self.zbfile:
            self.reportProgress('No zenbackup package provided..')
            raise EventImportError(Results.UNTAR_FAIL, -1)

        self._untarBackup()
        self._checkFiles()
        self.reportProgress('Success...')
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
        pass

    def _checkFiles(self):
        pass

