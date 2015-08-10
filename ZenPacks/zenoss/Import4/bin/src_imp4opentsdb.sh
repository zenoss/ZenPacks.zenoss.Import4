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

next_task()
{
    ( flock -w 120 9 || exit 1

      # atomically get and move the next task
      fn=$(ls -f1 /import4/Q.tsdb | awk '/task.*/ {print $0; exit}')

      if [[ -f /import4/Q.tsdb/"$fn" ]] 
      then
        mv "/import4/Q.tsdb/$fn" /import4/Q.tsdb/.tmp
        echo -n "/import4/Q.tsdb/.tmp/$fn"
      fi

    ) 9< /import4/Q.tsdb
}

#
# find the converted input file and import it
while true
do
    echo 'Rescanning tsdb files ...'

    ! check_monitor && sleep 5 && continue

    [[ ! -d /import4/Q.tsdb ]] && sleep 5 && continue

    job=$(next_task)
    if [[ -n "$job" ]] && [[ -f "$job" ]]
    then
        echo "Importing $job ..."
        /import4/pkg/bin/import_tsdb.sh "$job"
    else
        sleep 5
	    # check and revive the stuck tsdb
        /import4/pkg/bin/check_tsdb.sh
    fi

done
