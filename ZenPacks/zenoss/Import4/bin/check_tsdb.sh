#!/bin/bash
##############################################################################
#
# Copyright (C) Zenoss, Inc. 2014-2015, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

export tsdb_dir="/import4/Q.tsdb"   # the path to keep the final tsdb import files

# derived
export tsdb_tmp_dir="$tsdb_dir/.tmp"
export tsdb_done_dir="$tsdb_dir/.done"

# common block
progdir=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
source "$progdir/utils.sh"

# Not likely but we further monitor tsdb tmp dir and move back 
# other <tsdb_imp_file>'s no being completed for a while
# those files moved back will be picked up by imp4opentsdb.sh loop

# no need to check if not exist
[[ ! -d "$tsdb_tmp_dir" ]] && exit 0

find "$tsdb_tmp_dir" -maxdepth 1 -type f -mmin +5 | while read fname
do
   [[ -n "$fname" ]] && [[ -f "$fname" ]] && mv "$fname" "$tsdb_dir" 
done
