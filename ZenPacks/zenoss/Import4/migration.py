class ValidationResults(object):
    SUCCESS = 'SUCCESS'
    WARNING = 'WARNING'
    FAILURE = 'FAILURE'

exitCode = {
    ValidationResults.FAILURE: 2,
    ValidationResults.WARNING: 1,
    ValidationResults.SUCCESS: 0
}

class MigrationBase(object):
    def __init__(self, args, progressCallback):
        self.args = args
        self.progress = progressCallback

    def prevalidate(self):
        raise NotImplementedError
        return

    def wipe(self):
        raise NotImplementedError

    def doImport(self):
        raise NotImplementedError

    def reportProgress(self, progress):
        self.progress(progress)

    def postvalidate(self):
        raise NotImplementedError