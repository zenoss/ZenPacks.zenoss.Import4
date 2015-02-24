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
while read tfile
do
    echo "Importing $tfile ..."
    if [[ "$tfile" != "" ]]
    then
        /import4/pkg/bin/import_tsdb.sh "$tfile"
    else
        sleep 5
    fi
done < <(ls -1 /import4/Q.tsdb/task*.tsdb 2>/dev/null | head -n 1) 
