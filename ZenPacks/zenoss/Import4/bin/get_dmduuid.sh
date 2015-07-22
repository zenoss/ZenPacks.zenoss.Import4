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

if [ -f "$UUID_CACHE" ] 
then
    cat "$UUID_CACHE"
    exit $?
else
    echo 'Cannot get dmd.uuid! Need to service run imp4mariadb check <4x.tar> first.' >&2
    exit 1
fi
