#!/bin/bash
##############################################################################
#
# Copyright (C) Zenoss, Inc. 2014-2015, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

#
# The script is the starter script for imp4mariadb container
# There maybe multiple instances running at the same time
# task(s): perfdata conversion
#
echo "$0 Running ..."

export VOL_D='/import4'
export PYTHONPATH=$PYTHONPATH:$VOL_D/pkg
export PATH=$PATH:$VOL_D/pkg/bin

# common block
progdir=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
source "$progdir/utils.sh"

#
# find the converted input file and import it
while true
do
    echo 'Rescanning tsdb files ...'
    (( tno = 0 ))
    find /import4/Q.tsdb -maxdepth 1 -type f -name "task*.tsdb" -print | while read tfile
    do
        if [[ -n "$tfile" ]]
        then
            echo "Importing $tfile ..."
            (( tno += 1 ))
            /import4/pkg/bin/import_tsdb.sh "$tfile"
        fi
    done

    if [[ $tno -eq 0 ]]
    then
	        # check and revive the stuck tsdb
            /import4/pkg/bin/check_tsdb.sh
            sleep 5
    fi
done
