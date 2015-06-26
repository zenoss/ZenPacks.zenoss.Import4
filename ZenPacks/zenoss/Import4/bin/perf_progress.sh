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
export converted_Q=/import4/Q.jobs/.done   # completed
export converted_Q_fail=/import4/Q.jobs/.fail   # failed

export task_Q=/import4/Q.tsdb           # to be imported
export imported_Q=/import4/Q.tsdb/.done    # completed
export imported_Q_fail=/import4/Q.tsdb/.fail    # failed

export rrd_list=/import4/staging/zenbackup/perf/rrd.list

# common block
progdir=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
# echo "$progdir"
source "$progdir/utils.sh"

# check all the target directories
[[ -d $tasks_Q ]] || err_exit "$tasks_Q does not exist"
[[ -d $converted_Q ]] || mkdir -p "$converted_Q"
[[ -d $imported_Q ]] || mkdir -p "$imported_Q"

# the current conversion status
wait_no=$(find $tasks_Q -type f -name "task.*" -exec cat {} \; | wc -l)
converted_no=$(find $converted_Q -type f -name "task.*" -exec cat {} \; | wc -l)
tsum=$(cat "$rrd_list" | wc -l)
[[ $tsum -ne 0 ]] || err_exit "No task"

# started_no=$(find $jobs_Q -type f -name "task.*" -exec cat {} \; | wc -l)

# the current imported number
imported_no=$(find $imported_Q -type f -name "task.*.tsdb" -print | wc -l)
# Each tsdb file contains 5 rrd, but not exceeding the tsum
((imported_no=imported_no*5))
[ $imported_no -gt $tsum ] && ((imported_no=tsum))

# the total failure counts, not rrd count
fail_c_no=$(find $converted_Q_fail -type f -name "task.*" -print | wc -l)
fail_i_no=$(find $imported_Q_fail  -type f -name "task.*" -print | wc -l)
((fsum=fail_c_no+fail_i_no))

# the exact output format is important. 
echo "T:$tsum F:$fsum C:$converted_no D:$imported_no"
exit 0
