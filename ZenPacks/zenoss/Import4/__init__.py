##############################################################################
#
# Copyright (C) Zenoss, Inc. 2014-2015, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

import os
import Globals
import sys

from Products.ZenModel.ZenPack import ZenPack as ZenPackBase
from Products.ZenUtils.Utils import unused, zenPath

import logging

logger = logging.getLogger(__name__)
handler = logging.StreamHandler(stream=sys.stderr)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s:%(lineno)s: %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

unused(Globals)


class ZenPack(ZenPackBase):

    binFilesToSymlink = (
        'import4',
        )

    def install(self, dmd):
        super(ZenPack, self).install(dmd)
        self.postInstall()

    def postInstall(self):
        self.symlinkBinFiles()

    def symlinkBinFiles(self):
        for binFile in self.binFilesToSymlink:
            os.system('ln -sf %s/%s %s/' %
                      (self.path('bin'), binFile, zenPath('bin')))

    def remove(self, dmd, leaveObjects=False):
        super(ZenPack, self).remove(dmd, leaveObjects)
        self.postRemove()

    def postRemove(self):
        self.removeBinFileSymlinks()

    def removeBinFileSymlinks(self):
        for binFile in self.binFilesToSymlink:
            os.system('rm -rf %s/%s' % (zenPath('bin'), binFile))
