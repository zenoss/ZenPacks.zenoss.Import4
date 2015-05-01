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
# count the number of task files being processed + completed
#
export tasks_Q=/import4/Q.tasks         # initial all task lists

export jobs_Q=/import4/Q.jobs           # being processed + completed
export jdone_Q=/import4/Q.jobs/.done    # completed

export task_Q=/import4/Q.tsdb           # to be imported
export tdone_Q=/import4/Q.tsdb/.done    # completed

# common block
progdir=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
# echo "$progdir"
source "$progdir/utils.sh"

# check all the target directories
[[ -d $tasks_Q ]] || err_exit "$tasks_Q does not exist"
[[ -d $jdone_Q ]] || mkdir -p "$jdone_Q"
[[ -d $tdone_Q ]] || mkdir -p "$tdone_Q"

# the current conversion status
wait_no=$(find $tasks_Q -type f -name "task.*" | wc -l)
started_no=$(find $jobs_Q -type f -name "task.*" | wc -l)
jdone_no=$(find $jdone_Q -type f -name "task.*" | wc -l)
tsum=$((wait_no+started_no))
[[ $tsum -ne 0 ]] || err_exit "No task"

# the current imported number
imported_no=$(find $tdone_Q -type f -name "task.*.tsdb" | wc -l)
cent=$(((imported_no*100)/tsum))

# the exact output format is important
echo "T:$tsum S:$started_no C:$jdone_no D:$imported_no P:$cent"
exit 0
