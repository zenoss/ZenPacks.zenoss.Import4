# import argparse
from ZenPacks.zenoss.Import4.migration import MigrationBase


def init_command_parser(subparsers):
    # add specific arguments for events migration
    events_parser = subparsers.add_parser('events', help='migrate event data')
    return events_parser


class Migration(MigrationBase):
    def __init__(self, args, progressCallback):
        # common setup setup
        super(Migration, self).__init__(args, progressCallback)

    def prevalidate(self):
        self.__NOT_YET__()
        return

    def wipe(self):
        self.__NOT_YET__()
        return

    def wipe(self):
        self.__NOT_YET__()
        return

    def doImport(self):
        for i in [0, 10, 20, 30, 40, 50, 100]:
            self.progress("%d" % i)
        self.__NOT_YET__()
        return

    def reportProgress(self, progress):
        pass

    def postvalidate(self):
        self.__NOT_YET__()
        return
