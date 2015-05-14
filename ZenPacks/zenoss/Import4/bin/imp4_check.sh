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
cmd="cd /mnt/pwd; /opt/zenoss/bin/python /import4/pkg/bin/import4 -c "
(su - zenoss -c "$cmd model"            || (echo "Model files not valid!"            && exit 2)) || exit $?
(su - zenoss -c "$cmd events"           || (echo "Events files not valid!"           && exit 2)) || exit $?
(su - zenoss -c "$cmd perf --skip-scan" || (echo "Performance data files not valid!" && exit 2)) || exit $?

echo "Migration files checked OK..."
echo "No need to commit image for this operation..."
exit 1
