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
export tsdb_error="/import4/tsdb.err.log"   # keep the error output from telnet 4242
export tsdb_imp_file="$1"               # place where we kept the importing file
export tsdb_dir="/import4/Q.tsdb"   # the path to keep the final tsdb import files

# derived
export tsdb_base=$(basename "$tsdb_imp_file")

export tsdb_done_dir="$tsdb_dir/.done"
export tsdb_fail_dir="$tsdb_dir/.fail"

# common block
progdir=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
source "$progdir/utils.sh"

perf_out ()
{
  echo -e "$1" >> "$fail_records"
}

[[ -f "$tsdb_imp_file" ]] || err_exit "import file:$tsdb_imp_file not available"

# this process owns the $tsdb file

# mark the start time for revival in case this process died
touch "$tsdb_imp_file" 

[[ -f "$tsdb_error" ]] && rm "$tsdb_error"

# 30 seconds time out when import process stuck
timeout 30 awk -f "$progdir"/import_tsdb.awk "$tsdb_imp_file"

let rc=$?
if [[ $rc -ne 0 ]] 
then
    [[ -f "$tsdb_error" ]] && cat "$tsdb_error" >> "$fail_records"

    # if failed, move the tsdb file back and retry later
    # if a true error, the perf_progress monitoring will timeout 
    # then abort at the perf import level
    if [[ ! -d "$tsdb_fail_dir" ]]
    then
        mkdir -p "$tsdb_fail_dir"       || err_out "Cannot mkdir $tsdb_fail_dir"
        chmod -R 777 "$tsdb_fail_dir"   || err_out "Cannot chmod $tsdb_fail_dir"
    fi
    cp "$tsdb_imp_file" "$tsdb_fail_dir"    # for debug
    mv "$tsdb_imp_file" "$tsdb_dir"

    info_out "Import $tsdb_imp_file failed, will retry later ..."
    perf_out "[WARN] Import $tsdb_imp_file failed, will retry later ..." 

    exit 1
fi

# import_tsdb.awk will produce the quota used into /tmp/quota.used file
(
    flock -w 120 201 || exit 1
    _quota=$(cat "$idle.quota")
    echo -n $(( _quota-$(cat "/tmp/quota.used"))) > "$idle.quota"
) 201>"$idle.lock"

info_out "Quota: $(cat $idle.quota)"

# remove failed if succeeded this time
if [[ -f "$tsdb_fail_dir/$tsdb_base" ]]
then
    info_out "$tsdb_fail_dir/$tsdb_base retry succeeded"
    perf_out "[INFO] $tsdb_fail_dir/$tsdb_base retry succeeded"
    rm "$tsdb_fail_dir/$tsdb_base"
fi

# mark the process complete
touch "$tsdb_done_dir/$tsdb_base"

# remove the intermediate file
rm "$tsdb_imp_file" 
