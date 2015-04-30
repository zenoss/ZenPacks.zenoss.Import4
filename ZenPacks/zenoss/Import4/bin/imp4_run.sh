#! /usr/bin/env bash
##############################################################################
#
# Copyright (C) Zenoss, Inc. 2014, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

# use the mounted directory as the current directory
cmd="cd /mnt/pwd; /opt/zenoss/bin/python /import4/pkg/bin/import4 $*"
su - zenoss -c "$cmd"
let rc=$?

# if successful, patch the special conf file back to default port:3306
# before it is committed back to image
if [[ rc -eq 0 ]]
then
        sed -i -e 's/3307/3306/g' /opt/zenoss/etc/zodb_db_main.conf
fi
exit $rc
