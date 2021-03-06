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

tsum=$(cat "$rrd_list" | wc -l)
[[ $tsum -ne 0 ]] || err_exit "No task"

# the current conversion status
converted_no=$(find $converted_Q -type f -print | wc -l)
((converted_no=converted_no*rrds_per_task))
[ $converted_no -gt $tsum ] && ((converted_no=tsum))

# the current imported number
imported_no=$(find $imported_Q -type f -print | wc -l)
((imported_no=imported_no*rrds_per_task))
[ $imported_no -gt $tsum ] && ((imported_no=tsum))

# the total failure counts, not rrd count
[ -d "$converted_Q_fail" ] && ((fail_c_no=$(find $converted_Q_fail -type f -print | wc -l))) || ((fail_c_no=0))
[ -d "$imported_Q_fail" ]  && ((fail_i_no=$(find $imported_Q_fail  -type f -print | wc -l))) || ((fail_i_no=0))
((fsum=(fail_c_no+fail_i_no)*rrds_per_task))

# the exact output format is important. 
echo "T:$tsum F:$fsum C:$converted_no D:$imported_no"

exit 0
