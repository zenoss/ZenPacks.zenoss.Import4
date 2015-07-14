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
# try to lock/grab the given file
#   returns non-zero if not successful

export fail_records="/import4/perf.fail.records" # keep the failed status for top level UI
export tsdb_file="$1"                   # the absolute path to a tsdb import file 
export tsdb_dir="/import4/Q.tsdb"   # the path to keep the final tsdb import files

# derived
export tsdb_base=$(basename "$tsdb_file")

export tsdb_tmp_dir="$tsdb_dir/.tmp"
export tsdb_imp_file="$tsdb_tmp_dir/$tsdb_base"  # place where we kept the importing file
export tsdb_done_dir="$tsdb_dir/.done"
export tsdb_fail_dir="$tsdb_dir/.fail"

# common block
progdir=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
source "$progdir/utils.sh"

# check parameters and environment
mkdir -p "$tsdb_tmp_dir" 
mkdir -p "$tsdb_done_dir"
mkdir -p "$tsdb_fail_dir" 

[[ -f "$tsdb_file" ]]    || err_exit "import file:$tsdb_file not available anymore"
[[ -d "$tsdb_tmp_dir" ]] || err_exit "Working directory $tsdb_tmp_dir not available"

# double attempts for an atomic ownership
ln "$tsdb_file" "$tsdb_imp_file"    >/dev/null 2>&1 || err_exit "someone else got $tsdb_file - ln" 
touch "$tsdb_imp_file"              >/dev/null 2>&1 || err_exit "someone else got $tsdb_file - touch" 
sync
rm "$tsdb_file"             >/dev/null 2>&1 || err_exit "someone else got $tsdb_file - rm"
sync

# now this process owns the $tsdb file
timeout 120 /opt/opentsdb/build/tsdb import --config=/opt/zenoss/etc/opentsdb/opentsdb.conf "$tsdb_imp_file"

let rc=$?
if [[ $rc -eq 124 ]]
then
    echo "[Warning - timeout] $tsdb_imp_file" >> "$fail_records"
    # if time-out, move the tsdb file back
    mv -f "$tsdb_imp_file" "$tsdb_dir"

    exit 1
elif [[ $rc -ne 0 ]] 
then
    echo "[ERROR] $tsdb_imp_file" >> "$fail_records"

    # if failed, move the tsdb file to the failed dir 
    mv -f "$tsdb_imp_file" "$tsdb_fail_dir"
    sync

    exit 1
fi

# mark the process complete
mv "$tsdb_imp_file" "$tsdb_done_dir/$tsdb_base"
sync

