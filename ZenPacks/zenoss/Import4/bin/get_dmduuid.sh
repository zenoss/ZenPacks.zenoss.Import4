#!/usr/bin/bash
UUID_CACHE="/tmp/dmd_uuid.txt"

if [ ! -f "$UUID_CACHE" ]
then
    /opt/zenoss/bin/zendmd --script=<(echo -e "ofile=open('$UUID_CACHE','w')\nofile.write(dmd.uuid)\nofile.close()") 
    if [ $? -ne 0 ] || [ ! -f "$UUID_CACHE" ]
    then
        echo "Cannot get dmd.uuid ... \n" >&2
        exit 1
    fi
fi
cat "$UUID_CACHE"
exit $?
