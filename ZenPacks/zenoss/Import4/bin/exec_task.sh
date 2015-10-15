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
# the provided job is locked
#

# PERFTOP must be set and points to the top of the device tree
export task_dir="/import4/Q.tasks"  # the path keeping the unclaimed tasks

export job="$1"                    # the absolute path to a task file containing a rrdfiles list
export job_dir="/import4/Q.jobs"    # the path keeping the tasks being processed
export tsdb_dir="/import4/Q.tsdb"   # the path to keep the final tsdb import files
export fail_records="/import4/perf.fail.records" # keep the failed status for top level UI

# derived
export jobname=$(basename "$job")

export job_done_dir="$job_dir/.done"
export job_fail_dir="$job_dir/.fail"
export job_part_dir="$job_dir/.part"
export job_tmp_dir="$job_dir/.tmp"
export job_done="$job_done_dir/$jobname"

export job_raw="$job_tmp_dir/$jobname".tsdb.raw
export job_ok="$job_tmp_dir/$jobname".tsdb.ok

export tsdb_file="$tsdb_dir/$jobname".tsdb

# common block
progdir=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
source "$progdir/utils.sh"

# check parameters and environment
[[ -f "$task_dir/PERFTOP" ]] || err_exit "file:$task_dir/PERFTOP not created yet..."
read PERFTOP < "$task_dir/PERFTOP"
[[ -d "$PERFTOP" ]]     || err_exit "$PERFTOP location in \"$task_dir/PERFTOP\" is not correct"
[[ -d "$job_dir" ]]     || err_exit "Job directory not available"

# Not likely but we can further monitor workers and restart crashed ones
# <job> no being completed for a while

# now this process does own the $job
mkdir -p "$job_tmp_dir" 
mkdir -p "$job_fail_dir"
mkdir -p "$job_part_dir"
rm -f "$job_raw"   # cleanup first

info_out "Processing $job"

# the conversion time should be < 10 seconds
while read one_rrd
do
    "$progdir"/rrd2tsdb.sh "$PERFTOP" "$one_rrd" >> "$job_raw"
    let rc=$?
    if [[ $rc -ne 0 ]] 
    then
        echo "[ERROR] $one_rrd in $job" >> "$fail_records"

        # failed, send the partial result to the part pool for debug
        [ -f "$job_raw" ] && mv "$job_raw" "$job_part_dir"

        # put the faled job in the fail pool
        mv "$job" "$job_fail_dir"

        exit 1
    fi
done < "$job"

# make the finalized tsdb import file visible
mv "$job_raw" "$tsdb_file"

# mark job completed
mkdir -p "$job_done_dir"
mv "$job" "$job_done"
