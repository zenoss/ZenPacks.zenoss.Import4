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
which rrdtool || ( [[ -f /import4/pkg/bin/install_rrdtool.sh ]] && /import4/pkg/bin/install_rrdtool.sh )

# cache the uuid first
runuser -l zenoss -c /import4/pkg/bin/get_dmduuid.sh

# find the available task and execute it
while read task
do
    if [[ "$task" == "" ]]
    then
        sleep 5
    else
        echo "Trying $task ..."
        runuser -l zenoss -c "/import4/pkg/bin/exec_task.sh \"$task\""
    fi
done < <(ls -1 /import4/Q.tasks/task* | head -n 1) 
