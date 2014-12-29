class Results(object):
    SUCCESS = 'SUCCESS'
    WARNING = 'WARNING'
    FAILURE = 'FAILURE'

import inspect


class MigrationBase(object):
    def __init__(self, args, progressCallback):
        self.args = args
        self.progress = progressCallback
        self.tempDir = args.staging_dir
        self.file = args.file
        self.ip = args.ip
        self.user = args.user
        self.password = args.password

    def __NOT_YET__(self):
        caller = inspect.stack()[1]
        print "-- %s:%s:%s not implemented! --" % \
            (inspect.getmodule(caller[0]).__name__,
             self.__class__.__name__, caller[3])
        # raise NotImplementedError
        return

    def prevalidate(self):
        self.__NOT_YET__()
        print "-- To be overriden!"
        return

    def wipe(self):
        self.__NOT_YET__()
        print "-- To be overriden!"
        return

    def doImport(self):
        self.__NOT_YET__()
        print "-- To be overriden!"
        return

    def reportProgress(self, progress):
        # callback to self.progress if register at creation
        if self.progress:
            self.progress(progress)

    def postvalidate(self):
        self.__NOT_YET__()
        print "-- To be overriden!"
        return
