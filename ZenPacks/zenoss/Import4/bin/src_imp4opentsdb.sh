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
source "$progdir/utils.sh"

#
# find the converted input file and import it
while true
do
    echo 'Rescanning tsdb files ...'
    tsdbs=$(find /import4/Q.tsdb -maxdepth 1 -name "task*.tsdb" -print)
    if [[ -z "$tsdbs" ]]
    then
            sleep 5
    else
        for tfile in "$tsdbs"
        do
            echo "Importing $tfile ..."
            /import4/pkg/bin/import_tsdb.sh "$tfile"
        done
    fi
done
