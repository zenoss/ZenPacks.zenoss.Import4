#!/usr/bin/bash
##############################################################################
#
# Copyright (C) Zenoss, Inc. 2014-2015, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

UUID_CACHE="/import4/dmd_uuid.txt"
UUID_SRC="/mnt/pwd/dmd_uuid.txt"

[ -f "$UUID_SRC" ] && cp "$UUID_SRC" "$UUID_CACHE"

if [ ! -f "$UUID_CACHE" ]
then
    echo "Cannot get dmd.uuid ... \n" >&2
    exit 1
fi
cat "$UUID_CACHE"
exit $?
