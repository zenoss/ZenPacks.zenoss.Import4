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

# forcefully cleanup all the ongoing tasks/jobs

targets="
tasks
jobs
tsdb
"

# remove the save_dir if exist
save_dir="/import4/Q.save"
rm -rf "$save_dir"
rm -f "$fail_records"

for dname in $targets
do
    # remove the residue directories
    rm -rf "/import4/Q.$dname"

    # recreate the struct
    mkdir -p "/import4/Q.$dname/.done"
    chmod -R a+w "/import4/Q.$dname"
done
