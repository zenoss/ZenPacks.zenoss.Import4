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
    def __NOT_YET__(self):
        print "%s:%s is not implemented yet" % \
            (self.__class__.__name__, inspect.stack()[1][3])
        # raise NotImplementedError
        return

    def __init__(self, args, progressCallback):
        self.args = args
        self.progress = progressCallback

    def prevalidate(self):
        self.__NOT_YET__()
        return

    def wipe(self):
        self.__NOT_YET__()
        return

    def doImport(self):
        self.__NOT_YET__()
        return

    def reportProgress(self, progress):
        self.progress(progress)

    def postvalidate(self):
        self.__NOT_YET__()
        return
