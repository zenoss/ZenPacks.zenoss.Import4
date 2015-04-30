#!/bin/bash
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

# cache the uuid first
runuser -l zenoss -c /import4/pkg/bin/get_dmduuid.sh

# find the available task and execute it
while true
do
    echo 'Rescan tasks...'

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
        sleep 5
    fi
done