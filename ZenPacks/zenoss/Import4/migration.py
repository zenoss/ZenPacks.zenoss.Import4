##############################################################################
#
# Copyright (C) Zenoss, Inc. 2014-2015, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

import logging

class Results(object):
    SUCCESS = 'SUCCESS'
    WARNING = 'WARNING'
    FAILURE = 'FAILURE'


class Config(object):
    volume =        '/import4'
    pkgPath =       '/import4/pkg'
    pkgBinPath =    '/import4/pkg/bin'
    stageDir =      '/import4/staging'
    zenbackupDir =  '/import4/staging/zenbackup'
    perfDir =       '/import4/staging/zenbackup/perf'
    rrdTop =        '/import4/staging/zenbackup/perf/Devices'
    # content of a 4.x zenbackup file
    zepBackup =     'zenbackup/zep.sql.gz'
    zepSQL =        'zenbackup/zep.sql'
    zodbBackup =    'zenbackup/zodb.sql.gz'
    zodbSQL =       'zenbackup/zodb.sql'
    zenpackBackup = 'zenbackup/ZenPacks.tar'
    perfBackup =    'zenbackup/perf.tar'


import inspect


class ImportError(Exception):
    def __init__(self, error_string, return_code):
        self.return_code = return_code
        self.error_string = error_string


class MigrationBase(object):
    def __init__(self, args, progressCallback):
        log = logging.getLogger(__name__)
        self.args = args
        self.progress = progressCallback
        self.tempDir = args.staging_dir
        self.ip = args.ip
        self.user = args.user
        if args.password:
            self.password = args.password
        else:
            self.password = ''
        self.zbfile = args.zenbackup_file
        if args.log_level:
            logging.basicConfig(level=getattr(logging, args.log_level.upper()))

    def __NOT_YET__(self):
        caller = inspect.stack()[1]
        logging.warning("-- %s:%s:%s not implemented! --" %
            (inspect.getmodule(caller[0]).__name__, self.__class__.__name__, caller[3]))
        # raise NotImplementedError
        return

    def prevalidate(self):
        self.__NOT_YET__()
        logging.warning("-- To be overriden!" )
        return

    def wipe(self):
        self.__NOT_YET__()
        logging.warning("-- To be overriden!")
        return

    def doImport(self):
        self.__NOT_YET__()
        logging.warning("-- To be overriden!")
        return

    def reportProgress(self, progress):
        # callback to self.progress if register at creation
        logging.debug(progress)
        if self.progress:
            self.progress(progress)

    def postvalidate(self):
        self.__NOT_YET__()
        logging.warning("-- To be overriden!")
        return
