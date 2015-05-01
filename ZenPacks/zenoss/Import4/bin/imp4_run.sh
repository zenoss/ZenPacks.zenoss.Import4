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

# check to see if we need to commit the image
[[ $rc != 0 ]] && exit $rc

options="__OPTIONS__: $*"
for op in ' -h ' ' --help' 
do
    if [[ "$options" == *"$op"* ]]
    then
        # no need to commit the image for help commands
        exit 1
    fi
done

# commit only when it is for successful model import operation
for op in ' -x ' ' --import' 
do
    if [[ "$options" == *"$op"* ]]
    then
        [[ "$options" != *" model"* ]] && continue
        # patch the special conf file back to default port:3306
        sed -i -e 's/3307/3306/g' /opt/zenoss/etc/zodb_db_main.conf
        # allow serviced service run to commit
        exit 0
    fi
done

echo "No need to commit image for this operation..."
exit 1
