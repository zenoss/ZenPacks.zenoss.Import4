#!/bin/bash
#
# try to lock/grab the given file
#   returns non-zero if not successful

export tsdb_dir="/import4/Q.tsdb"   # the path to keep the final tsdb import files

# derived
export tsdb_tmp_dir="$tsdb_dir/.tmp"
export tsdb_done_dir="$tsdb_dir/.done"

# common block
progdir=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
source "$progdir/utils.sh"

# check parameters and environment
mkdir -p "$tsdb_tmp_dir" 
chmod -R 777 "$tsdb_dir"

# Not likely but we further monitor tsdb tmp dir and move back 
# other <tsdb_imp_file>'s no being completed for a while
# those files moved back will be picked up by imp4opentsdb.sh loop
find "$tsdb_tmp_dir" -maxdepth 1 -type f -mmin +5 | while read fname
do
   [[ -n "$fname" ]] && mv "$fname" "$tsdb_dir" 
done
