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

check_services()
{
    # check opentsdb
    echo "Checking services ..."
    if ! timeout 5 wget -q -O - http://127.0.0.1:4242/api/stats > /dev/null  
    then
        echo "opentsdb-writer not running!"
        return 1
    fi

    # may need to check region server cluster in the future for stability

    echo "depending services OK..."
    return 0
}

# make sure that the environment has gawk installed
which gawk || apt-get install gawk
which gawk || err_exit "Cannot install GNU awk"

#
# find the converted input file and import it
while true
do
    echo 'Importer loop start ...'

    ! check_monitor && sleep 5 && continue

    [[ ! -d /import4/Q.tsdb ]] && sleep 5 && continue

    # if CPU is busy
    ! check_idle && sleep 5 && continue

    # check if depending services are ready
    ! check_services && sleep 10 && continue

    # check if tsdb quota is enough
    ! check_quota && sleep 10 && continue

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

    # if monitor terminated, the import loop is done
    ! check_monitor && exit 1
done
