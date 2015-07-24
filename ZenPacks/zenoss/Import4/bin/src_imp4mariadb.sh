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
export ptag='/import4/staging/polling'

# common block
progdir=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
source "$progdir/utils.sh"

# set the correct ports for zodb
cp  -p /opt/zenoss/etc/zodb_db_imp4.conf /opt/zenoss/etc/zodb_db_main.conf

# after a cycle
# depending on serviced to restart the service

# pre install in each container
while ! which rrdtool 
do
   if [[ -f /import4/pkg/bin/install_rrdtool.sh ]]
   then
       /import4/pkg/bin/install_rrdtool.sh > /opt/zenoss/log/install_rrdtool.log 2>&1
   else
       sleep 5
   fi
done

# cache the uuid first. This needs to be 'after' model import
runuser -l zenoss -c /import4/pkg/bin/get_dmduuid.sh

# find the available task and execute it
while true
do
    echo 'Rescan tasks...'

    # check if the monitor is alive
    if [[ ! -f "$ptag" ]] 
    then
        echo 'Performance data import process not started yet...'
        sleep 5
        continue
    fi

    # if monitor is dead (300 seconds), abort all operation
    if (( ($(date +"%s")-$(stat --printf="%Y" "$ptag")) > 300 )) 
    then
        echo 'Performance data import process stopped, cleaning up... '
        rm -f "$ptag"
        /import4/pkg/bin/abort_jobs.sh
        echo 'Task queues removed...'
        continue
    fi

    (( fno = 0 ))
    find /import4/Q.tasks -maxdepth 1 -type f -name "task*" -print | while read task
    do
        if [[ -n "$task" ]]
        then
            (( fno += 1))
            echo "Trying $task ..."
            runuser -l zenoss -c "/import4/pkg/bin/exec_task.sh \"$task\""
        fi 
    done

    if [[ $fno -eq 0 ]]
    then
	    # check and revive the stuck tasks
        runuser -l zenoss -c "/import4/pkg/bin/check_task.sh"
    fi
done
