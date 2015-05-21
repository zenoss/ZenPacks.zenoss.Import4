#!/usr/bin/bash
##############################################################################
#
# Copyright (C) Zenoss, Inc. 2014-2015, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

# this script is to be no-op'd once this file is included in the expor4 output
UUID_CACHE="/mnt/pwd/dmd_uuid.txt"

# updates the dmd uuid to the cache location
/opt/zenoss/bin/zendmd --script=<(echo -e "ofile=open('$UUID_CACHE','w')\nofile.write(dmd.uuid)\nofile.close()" )

if [ $? -ne 0 ] || [ ! -f "$UUID_CACHE" ]
then
    echo "Cannot get dmd.uuid ... \n" >&2
    exit 1
fi

cat "$UUID_CACHE"
exit $?
