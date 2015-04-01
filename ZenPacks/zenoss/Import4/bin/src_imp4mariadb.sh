#!/bin/bash -x
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
which rrdtool || ( [[ -f /import4/pkg/bin/install_rrdtool.sh ]] && /import4/pkg/bin/install_rrdtool.sh )

# cache the uuid first
runuser -l zenoss -c /import4/pkg/bin/get_dmduuid.sh

# find the available task and execute it
while true
do
    echo 'Rescan tasks...'
    tasks=$(find /import4/Q.tasks -maxdepth 1 -name "task*" -print)
    if [[ -z "$tasks" ]]
    then
	# check and revive the stuck tasks
        runuser -l zenoss -c "/import4/pkg/bin/check_task.sh"
        sleep 5
    else
	    for task in "$tasks"
	    do
            echo "Trying $task ..."
            runuser -l zenoss -c "/import4/pkg/bin/exec_task.sh \"$task\""
	    done
    fi
done
