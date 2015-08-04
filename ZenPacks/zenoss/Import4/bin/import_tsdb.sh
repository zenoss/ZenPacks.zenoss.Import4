#!/bin/bash
##############################################################################
#
# Copyright (C) Zenoss, Inc. 2014-2015, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

export fail_records="/import4/perf.fail.records" # keep the failed status for top level UI
export tsdb_imp_file="$1"               # place where we kept the importing file
export tsdb_dir="/import4/Q.tsdb"   # the path to keep the final tsdb import files

# derived
export tsdb_base=$(basename "$tsdb_imp_file")

export tsdb_tmp_dir="$tsdb_dir/.tmp"
export tsdb_done_dir="$tsdb_dir/.done"
export tsdb_fail_dir="$tsdb_dir/.fail"

# common block
progdir=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
source "$progdir/utils.sh"

[[ -f "$tsdb_imp_file" ]] || err_exit "import file:$tsdb_imp_file not available"

# this process owns the $tsdb file
timeout 120 /opt/opentsdb/build/tsdb import --config=/opt/zenoss/etc/opentsdb/opentsdb.conf "$tsdb_imp_file" 2>&1 | egrep "(TextImporter: Processed|ERROR)"

let rc=$?
if [[ $rc -eq 124 ]]
then
    echo "[Warning - timeout] $tsdb_imp_file" >> "$fail_records"
    # if time-out, move the tsdb file back and retry later
    mv "$tsdb_imp_file" "$tsdb_dir"

    exit 1
elif [[ $rc -ne 0 ]] 
then
    echo "[ERROR] $tsdb_imp_file" >> "$fail_records"

    # if failed, move the tsdb file back and retry later
    # if a true error, the perf_progress monitoring will timeout 
    # then abort at the perf import level
    cp "$tsdb_imp_file" "$tsdb_fail_dir"    # for debug
    mv "$tsdb_imp_file" "$tsdb_dir"

    exit 1
fi

# mark the process complete
mv "$tsdb_imp_file" "$tsdb_done_dir/$tsdb_base"

