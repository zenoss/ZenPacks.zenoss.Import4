#!/bin/bash
#
# try to lock/grab the given file
#   returns non-zero if not successful

export tsdb_file="$1"                   # the absolute path to a tsdb import file 
export tsdb_dir="/import4/Q.tsdb"   # the path to keep the final tsdb import files

# derived
export tsdb_base=$(basename "$tsdb_file")

export tsdb_tmp_dir="$tsdb_dir/.tmp"
export tsdb_imp_file="$tsdb_tmp_dir/$tsdb_base"  # place where we kept the importing file
export tsdb_done_dir="$tsdb_dir/.done"

# common block
progdir=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
source "$progdir/utils.sh"

# check parameters and environment
mkdir -p "$tsdb_tmp_dir" 

[[ -f "$tsdb_file" ]]    || err_exit "import file:$tsdb_file not available anymore"
[[ -d "$tsdb_tmp_dir" ]] || err_exit "Working directory $tsdb_tmp_dir not available"

# double attempts for an atomic ownership
ln "$tsdb_file" "$tsdb_imp_file"    >/dev/null 2>&1 || err_exit "someone else got $tsdb_file - ln" 
touch "$tsdb_imp_file"              >/dev/null 2>&1 || err_exit "someone else got $tsdb_file - touch" 
sync
rm "$tsdb_file"             >/dev/null 2>&1 || err_exit "someone else got $tsdb_file - rm"
sync

# now this process owns the $tsdb file
/opt/opentsdb/build/tsdb import --config=/opt/zenoss/etc/opentsdb/opentsdb.conf "$tsdb_imp_file"

let rc=$?
if [[ $rc -ne 0 ]] 
then
    # if failed, return the tsdb file back 
    mv "$tsdb_imp_file" "$tsdb_file"
    sync

    exit 1
fi

# mark the process complete
mkdir -p "$tsdb_done_dir"
mv "$tsdb_imp_file" "$tsdb_done_dir/$tsdb_base"
sync

