#! /usr/bin/env bash
##############################################################################
#
# Copyright (C) Zenoss, Inc. 2014-2015, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

export fail_records="/import4/perf.fail.records" # keep the failed status for top level UI

# common block
progdir=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
source "$progdir/utils.sh"

# save all the ongoing tasks/jobs at abort
targets="
tasks
jobs
tsdb
"

save_dir="/import4/Q.save"
rm -rf "$save_dir"
mkdir -p  "$save_dir"
chmod -R a+w "$save_dir"
[ -f "$fail_records" ] && mv "$fail_records" "$save_dir"

# the extra one for tsdb
mkdir -p "/import4/Q.tsdb/.tmp"
mkdir -p "/import4/Q.tsdb/.fail"

for dname in $targets
do
    # remove the residue directories
    mv "/import4/Q.$dname" "$save_dir"

    # recreate the struct
    mkdir -p "/import4/Q.$dname/.done"
    chmod -R a+w "/import4/Q.$dname"
    chown -R zenoss:zenoss "/import4/Q.$dname"
done

info_out "Performance directories cleaned up"
