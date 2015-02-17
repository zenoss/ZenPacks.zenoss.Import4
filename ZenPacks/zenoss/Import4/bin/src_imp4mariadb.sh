#!/bin/bash
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
. "$progdir/utils.sh"

# after a cycle
# depending on serviced to restart the service

# pre install in each container
which rrdtool || /import4/pkg/bin/install_rrdtool.sh

# find the available task and execute it
while read task
do
    echo "Trying $task ..."
    /import4/pkg/bin/exec_task.sh "$task"
done < <(ls /import4/Q.tasks/task* | head -n 1) 
