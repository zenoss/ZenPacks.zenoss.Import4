#! /usr/bin/env bash
##############################################################################
#
# Copyright (C) Zenoss, Inc. 2014, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

# prep the config for the running environment for zencommands (zodb)
cp  -p /opt/zenoss/etc/zodb_db_main.conf /tmp/zodb_db_main.conf.sav
cp  -p /opt/zenoss/etc/zodb_db_imp4.conf /opt/zenoss/etc/zodb_db_main.conf

# use the mounted directory as the current directory
cmd="cd /mnt/pwd; /opt/zenoss/bin/python /import4/pkg/bin/import4 $*"
su - zenoss -c "$cmd"
let rc=$?

# restore the config file
cp  -p /tmp/zodb_db_main.conf.sav /opt/zenoss/etc/zodb_db_main.conf

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
if [[ "$options" == *" import "* ]]; then
    [[ "$options" != *" model"* ]] && continue
    exit 0
fi

echo "No need to commit image for this operation..."
exit 1
