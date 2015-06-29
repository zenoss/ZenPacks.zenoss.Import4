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
# try to lock/grab the given task
#   returns non-zero if not successful

# PERFTOP must be set and points to the top of the device tree
export task="$1"                    # the absolute path to a task file containing a rrdfiles list
export task_dir="/import4/Q.tasks"  # the path keeping the unclaimed tasks
export job_dir="/import4/Q.jobs"    # the path keeping the tasks being processed
export tsdb_dir="/import4/Q.tsdb"   # the path to keep the final tsdb import files
export fail_records="/import4/perf.fail.records" # keep the failed status for top level UI

# derived
export taskname=$(basename "$task")

export job="$job_dir/$taskname"
export job_done_dir="$job_dir/.done"
export job_fail_dir="$job_dir/.fail"
export job_part_dir="$job_dir/.part"
export job_done="$job_done_dir/$taskname"

export tsdb_tmp_dir="$tsdb_dir/.tmp"
export tsdb_raw="$tsdb_tmp_dir/$taskname".tsdb.raw
export tsdb_ok="$tsdb_tmp_dir/$taskname".tsdb.ok
export tsdb_file="$tsdb_dir/$taskname".tsdb

# common block
progdir=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
source "$progdir/utils.sh"

# check parameters and environment
[[ -f "$task_dir/PERFTOP" ]] || err_exit "file:$task_dir/PERFTOP not created yet..."
read PERFTOP < "$task_dir/PERFTOP"
[[ -d "$PERFTOP" ]]     || err_exit "$PERFTOP location in \"$task_dir/PERFTOP\" is not correct"

[[ -f "$task" ]]        || err_exit "task:$task not available anymore"
[[ -d "$job_dir" ]]     || err_exit "Job directory not available"

# double attempts for an atomic ownership
ln "$task" "$job" >/dev/null 2>&1  || err_exit "someone else got $task - ln" 
touch "$job"      >/dev/null 2>&1  || err_exit "someone else got $task - touch" 
sync
rm "$task"        >/dev/null 2>&1  || err_exit "someone else got $task - rm"
sync

# Not likely but we can further monitor workers and restart crashed ones
# <job> no being completed for a while

# now this process does own the $job
mkdir -p "$tsdb_tmp_dir" 
mkdir -p "$job_fail_dir"
mkdir -p "$job_part_dir"
rm -f "$tsdb_raw"   # cleanup first
sync

while read one_rrd
do
    "$progdir"/../rrd2tsdb.py -p "$PERFTOP" "$one_rrd" >> "$tsdb_raw"
    let rc=$?
    if [[ $rc -ne 0 ]] 
    then
        echo "[ERROR] $one_rrd in $job" >> "$fail_records"

        # failed, send the partial result to the part pool for debug
        [ -f "tsdb_raw" ] && mv "$tsdb_raw" "$job_part_dir"

        # put the faled job in the fail pool
        mv "$job" "$job_fail_dir"
        sync

        exit 1
    fi
done < "$job"

# if successful
# we need to do a sort and uniq to resolve out-of-order and dup rrd data
# this is only needed when placed in the same import file
# this also filter out empty lines
sort "$tsdb_raw" | awk '(NF>0) && (!x[$1 $2]++)' > "$tsdb_ok"

# make the finalized tsdb import file visible
ln "$tsdb_ok" "$tsdb_file"

# cleanup
rm -f "$tsdb_raw" "$tsdb_ok"

# mark job completed
mkdir -p "$job_done_dir"
mv "$job" "$job_done"
sync
