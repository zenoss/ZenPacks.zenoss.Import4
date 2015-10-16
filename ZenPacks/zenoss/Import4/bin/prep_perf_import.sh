#! /bin/bash
##############################################################################
#
# Copyright (C) Zenoss, Inc. 2014-2015, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

# executed as root
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

# save the last run info
if [[ -d "$save_dir" ]] 
then
    rm -rf "$save_dir"
fi

mkdir -p  "$save_dir"
[ -f "$fail_records" ] && mv "$fail_records" "$save_dir"

for dname in $targets
do
    # remove the residue directories
    mv "/import4/Q.$dname" "$save_dir"

    # recreate the struct
    mkdir -p "/import4/Q.$dname/.done"
    mkdir -p "/import4/Q.$dname/.tmp"
    mkdir -p "/import4/Q.$dname/.fail"
    mkdir -p "/import4/Q.$dname/.part"
    chmod -R 777 "/import4/Q.$dname"
done

# print out the dir structures
find /import4 -maxdepth 2 -type d -printf "%M %u %p\n"

info_out "Performance directories cleaned up"
