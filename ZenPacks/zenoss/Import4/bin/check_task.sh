#!/bin/bash
#
# try to lock/grab the given task
#   returns non-zero if not successful

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

# search the job dir and forcefully move back the jobs stuck more than 5 min
find "$job_dir" -maxdepth 1 -type f -mmin +5 | while read fname
do
    [[ -n "fname" ]]  && mv "$fname" "$task_dir"
done
