#!/usr/bin/bash
##############################################################################
#
# Copyright (C) Zenoss, Inc. 2014-2015, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################


# common block
progdir=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
source "$progdir/utils.sh"

# the ZenPacks dir is passed in as the first argument
zps_dir="$1"
[[ -d "$zps_dir" ]]  || err_exit "No zenpack directory found ..."

# for each egg dir, create an egg for it
find "$zps_dir" -maxdepth 1 -type d -name "*.egg" -exec $progdir/zip_an_egg.sh {} \; 

# copy it to the .ZenPack dir
find "$zps_dir" -type f -name "*.egg" -exec cp -v {} /opt/zenoss/.ZenPacks \; 
