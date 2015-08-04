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
# PERFTOP must be set and points to the top of the device tree
export task_dir="/import4/Q.tasks"  # the path keeping the unclaimed tasks
export job_dir="/import4/Q.jobs"    # the path keeping the tasks being processed

# common block
progdir=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
source "$progdir/utils.sh"

# check parameters and environment
[[ -f "$task_dir/PERFTOP" ]] || err_exit "file:$task/PERFTOP not exist"
read PERFTOP < "$task_dir/PERFTOP"
[[ -d "$PERFTOP" ]]     || err_exit "$PERFTOP location in \"$task_dir/PERFTOP\" is not correct"
[[ -d "$job_dir" ]]     || err_exit "Job directory not available"

# search the job dir and forcefully move back the jobs stuck for more than 2 min
# The normal conversion time of a task is < 10 seconds
# it is considered abandand or failed by the owning processes
# no need to lock Q.tasks since we are adding to, not removing from the list

find "$job_dir" -maxdepth 1 -type f -mmin +2 | while read fname
do
    [[ -n "$fname" ]] && [[ -f "$fname" ]]  && mv "$fname" "$task_dir"
done
