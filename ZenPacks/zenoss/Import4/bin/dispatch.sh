#!/bin/bash
#
# This script starts the processing of rrdfiles by placing
# chunks of tasks (files containing list of rrdfile names)
# into a task directory monitored by the converter workers.
#
# This script is to be run once per rrd import for the source rrd tree
#
export rrdtop="$1"          # top directory (in absolute path) of the source rrd tree
export tasktop="$2"         # task queue directory for the rrd file lists (also in absolute path)

# derived
export tasktmp="$2/.tmp"

# common block
progdir=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
source "$progdir/utils.sh"

# finds all the rrd files and group them into task files
# The result is placed into the provied task queue directory
# The target directory is cleaned first

if [[ ! -d "$rrdtop" ]] 
then
    echo "Usage: $0 <rrd_dir> <task_dir>" >&2
    err_exit "rrd directory '$rrdtop' does not exist ..." 
fi

# prep the target dirs
mkdir -p "$tasktmp"                                                     || err_exit "Cannot create $tasktop and $tasktmp"

# clean up the target directory
rm -rf "$tasktop"/task.*                                                     || err_exit "Cannot remove files under $tasktop" 
rm -rf "$tasktmp"                                                       || err_exit "Cannot remove $tasktmp"

# finish preparing the tasks first before moving them to the final dir
# Assertion:
# if a task file exists under tasktop, no more change will be made to it
mkdir -p "$tasktmp"                                                     || err_exit "Cannot create $tasktop or $tasktmp"
find "$rrdtop" -type f -name "*.rrd" | split -l 5 - "$tasktmp"/task.    || err_exit "Error generating tasks"
mv "$tasktmp"/* "$tasktop"                                              || err_exit "No result tasks or error moving tasks"
rm -rf "$tasktmp"                                                       || err_exit "Error cleaning up $tasktmp"
sync

exit 0
