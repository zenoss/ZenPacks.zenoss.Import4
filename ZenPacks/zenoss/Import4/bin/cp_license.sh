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

# the license dir is fixed
src_dir="/mnt/pwd/flexera"
lic_dir="/opt/zenoss/var/flexera"

[ -d "$src_dir" ] && [ -d "$lic_dir" ] && cp -vrp "$src_dir/"* "$lic_dir" 
[ $? -ne 0 ] && err_exit "Error in copying license files"

# update dmd with migrated licenses
echo "getFacade('ucsxskin').get_license_info(refresh=True)" | zendmd

info_out "License files copied"
