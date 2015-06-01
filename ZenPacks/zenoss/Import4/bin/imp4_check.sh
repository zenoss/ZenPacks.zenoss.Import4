#! /usr/bin/env bash
##############################################################################
#
# Copyright (C) Zenoss, Inc. 2014, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

# prep the config for the running environment for zencommands (zodb)
cp  -p /opt/zenoss/etc/zodb_db_main.conf /tmp/zodb_db_main.conf.sav
cp  -p /opt/zenoss/etc/zodb_db_imp4.conf /opt/zenoss/etc/zodb_db_main.conf

# common block
progdir=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
source "$progdir/utils.sh"

cd /mnt/pwd

# check if the backup file is available
[[ ! -f "$1" ]] && err_exit "Migration file not found!"

# make sure /mnt/pwd is world r/w/x
if [[ $(find /mnt/pwd -maxdepth 0 -perm -777 | wc -l) != 1 ]]; then
    err_exit "Backup's parent directory is not world r/w/x - exiting"
fi

export imp4dir="/import4"
export staging_dir="$imp4dir/staging"
export staging_zenbackup_dir="$staging_dir/zenbackup"
export zbk="zenbackup"
export awk_cmd='{ if (NR%10 == 0) printf "."} END {printf "\n"}'

# removing previous artifacts
for i in \
        MODEL_* \
        PERF_* \
        EVENTS_* \
        _zen* \
        componentList.txt \
        zenbackup_*.tgz \
        zep.sql* \
        zodb.sql* \
        ZenPacks* \
        zencatalogservice* \
        perf.tar \
        dmd_uuid.txt \
        "$staging_dir"
do
    info_out "Removing $i"
    rm -rf "$i"
done

# extracting known data files from the tar ball
info_out "Extract zenbackup files" 
! tar -vxf "$1" >&2              && err_exit "Extracting zenbackup failed!"
! tar -zvxf zenbackup_*.tgz  >&2 && err_exit "Extracting zenbackup_*.tgz failed!"

info_out "Copy dmd_uuid.txt" 
cp dmd_uuid.txt /import4/dmd_uuid.txt || err_exit "Cannot get dmd_uuid.txt"

! cd "$zbk" && err_out "Invalid zenbackup file!"

# cleanup target files
! gunzip -vf "zep.sql.gz" >&2   && err_exit "Uncompressing zep.sql failed!"
! gunzip -vf "zodb.sql.gz" >&2  && err_exit "Uncompressing zodb.sql failed!"

info_out "Extracting ZenPacks.tar"
tar -vxf ZenPacks.tar | awk "$awk_cmd" >&2
[[ ${PIPESTATUS[0]} -ne 0 ]] && err_exit "Extracting ZenPack.tar failed!"

info_out "Extracting zencatalogservice.tar"
tar -vxf zencatalogservice.tar | awk "$awk_cmd" >&2
[[ ${PIPESTATUS[0]} -ne 0 ]] && err_exit "Extracting zencatalogservice.tar failed!"

info_out "Extracting zep.tar..."
tar -vxf zep.tar 2>/dev/null | awk "$awk_cmd" >&2
[[ ${PIPESTATUS[0]} -ne 0 ]] && info_out "Zeneventserver indexes not found, skipping"

# make sure dmd_uuid.txt is there!
if [[ ! -f ../dmd_uuid.txt ]]; then
    err_exit "dmd_uuid.txt is missing from backup, cannot continue"
fi

# extract the perf into the shared staging volume
! mkdir -p "$staging_zenbackup_dir" && err_exit "Cannot create staging directory in the containter!"

info_out "Extracting performance data tends to take a long time"
tar -C "$staging_zenbackup_dir" -vxf perf.tar | awk "$awk_cmd" >&2
[[ ${PIPESTATUS[0]} -ne 0 ]] && err_exit "Extracting performance data from perf.tar failed!"

info_out "Setup proper access right"
(find . -type d -exec chmod a+rwx {} \; >&2) &
(find . -type f -exec chmod a+rw {} \; >&2) &
(find "$staging_dir" -type d -exec chmod a+rwx {} \; >&2) &
(find "$staging_dir" -type f -exec chmod a+rw {} \; >&2) &
wait

# use the mounted directory as the current directory
# no redirect of stdout where meta data is reported
cmd="cd /mnt/pwd; /opt/zenoss/bin/python /import4/pkg/bin/import4 "
! su - zenoss -c "$cmd model check"            && err_exit "Model files not valid!"
! su - zenoss -c "$cmd events check"           && err_exit "Events files not valid!"
! su - zenoss -c "$cmd perf --skip-scan check" && err_exit "Performance data files not valid!"

info_out "Migration files checked OK..."
info_out "No need to commit image for this operation..."
exit 42
