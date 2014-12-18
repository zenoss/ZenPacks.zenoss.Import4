class ValidationResults(object):
    SUCCESS = 'SUCCESS'
    WARNING = 'WARNING'
    FAILURE = 'FAILURE'

import inspect

exitCode = {
    ValidationResults.FAILURE: 2,
    ValidationResults.WARNING: 1,
    ValidationResults.SUCCESS: 0,
    None: -1    # when the method has not been implemented
}


class MigrationBase(object):
    def __init__(self, args, progressCallback):
        self.args = args
        self.progress = progressCallback

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
        self.progress(progress)
        print "-- To be overriden!"

    def postvalidate(self):
        self.__NOT_YET__()
        print "-- To be overriden!"
        return
