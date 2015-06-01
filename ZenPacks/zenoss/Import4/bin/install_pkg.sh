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
# copy the executables/scripts for the sqlworker and tsdbworker scripts 
# the installation dir is fixed to volume /import4/pkg
#

export VOL_D='/import4'
export PKG_D="$VOL_D/pkg"
export BIN_D="$VOL_D/pkg/bin"

# common block
progdir=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
source "$progdir/utils.sh"

info_out "Installing import4 worker scripts from $progdir ..."

[[ -d "$VOL_D" ]]     || err_exit "The environment does not have the shared volume: $VOL_D" 
mkdir -p "$BIN_D"     || err_exit "Cannot create the pkg directories"

# copy the scripts
chmod +x "$progdir"/../*.py         || err_exit "Error chmod python scripts"
cp -p "$progdir"/../*.py "$PKG_D"   || err_exit "Error copying python scripts"
chmod +x "$progdir"/*               || err_exit "Error chmod bash scripts"
cp -p "$progdir"/*    "$BIN_D"      || err_exit "Error copying bash scripts"

chmod -R a+w "$PKG_D"
sync

# now move the worker scripts so the services can start
mv "$BIN_D/src_imp4mariadb.sh"    "$BIN_D/imp4mariadb.sh"   || err_exit "Error copying perfdata converter worker script"
mv "$BIN_D/src_imp4opentsdb.sh"   "$BIN_D/imp4opentsdb.sh"  || err_exit "Error copying opentsdb import worker script"
sync

# clean up staging areas
for i in 'Q.jobs'  'Q.tasks'  'Q.tsdb'  'staging'  'tmp' 'dmd_uuid.txt'
do
    rm -rf "/import4/$i"
done

info_out "Import4 scripts Installed!"
exit 0
