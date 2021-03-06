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
# It runs as root
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

# atomically print the next job or block 
next_task()
{
    ( flock -w 120 9 || exit 1

      # atomically get and move the next task
      fn=$(ls -f1 /import4/Q.tasks | awk '/task.*/ {print $0; exit}')

      if [[ -f /import4/Q.tasks/"$fn" ]] 
      then
        mv "/import4/Q.tasks/$fn" /import4/Q.jobs
        echo -n "/import4/Q.jobs/$fn"
      fi

    ) 9< /import4/Q.tasks
}

# set the correct ports for zodb
cp  -p /opt/zenoss/etc/zodb_db_imp4.conf /opt/zenoss/etc/zodb_db_main.conf

# cache the uuid first. This needs to be 'after' model import
runuser -l zenoss -c /import4/pkg/bin/get_dmduuid.sh

# find the available task and execute it
while true
do
    echo 'Conversion loop start ... '

    [[ ! -d /import4/Q.tasks ]] && sleep 5 && continue

    # check if perf import started
    ! check_monitor && sleep 5 && continue

    # check if importer is catching up
    ! check_pile && sleep 5 && continue

    # check CPU is busy
    ! check_idle && sleep 5 && continue

    job=$(next_task)
    if [[ -n "$job" ]] && [[ -f "$job" ]]
    then
        echo "Processing $job ..."
        runuser -l zenoss -c "/import4/pkg/bin/exec_task.sh \"$job\""
    else
	    # check and revive the stuck tasks
        sleep 5
        runuser -l zenoss -c "/import4/pkg/bin/check_task.sh"
    fi

    # if monitor terminated, the import loop is done
    ! check_monitor && exit 0

done
