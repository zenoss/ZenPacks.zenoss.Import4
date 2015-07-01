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

status_out ()
{
  echo "{ \"imp4_status\" : { \"check\" : \"$1\" }}"
  info_out "$1"
}
export -f status_out

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
status_out "Removing artifacts"
for i in \
        backup.md5 \
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
        perf.tar* \
        dmd_uuid.txt \
        "$staging_dir"
do
    info_out "Removing $i"
    rm -rf "$i"
done

# extracting known data files from the tar ball
status_out "Extracting $1" 
! tar -vxf "$1" >&2              && err_exit "Extracting zenbackup failed!"

if [[ -f backup.md5 ]]; then
   status_out "Check md5sum against backup.md5"
   cmp -s -n 32 backup.md5 <(md5sum -b zenbackup_*.tgz) && info_out "md5sum OK" || err_out "md5sum failed: zenbackup_*.tgz"
else
    info_out "No md5 checksum, continue"
fi

status_out "Extracting zenbackup.tgz"
! tar -zvxf zenbackup_*.tgz  >&2 && err_exit "Extracting zenbackup_*.tgz failed!"

# make sure dmd_uuid.txt is there!
status_out "Copying dmd_uuid.txt"
if [[ ! -f dmd_uuid.txt ]]; then
    err_exit "dmd_uuid.txt is missing from backup, cannot continue"
fi
cp dmd_uuid.txt /import4/dmd_uuid.txt || err_exit "Cannot get dmd_uuid.txt"

! cd "$zbk" && err_out "Invalid zenbackup file!"

# model files (zodb and zenpacks) are required 
status_out "Unzipping zodb.sql.gz"
! gunzip -vf "zodb.sql.gz" >&2  && err_exit "Uncompressing zodb.sql failed!"

status_out "Extracting ZenPacks.tar"
tar -vxf ZenPacks.tar | awk "$awk_cmd" >&2
[[ ${PIPESTATUS[0]} -ne 0 ]] && err_exit "Extracting ZenPack.tar failed!"

# events file is optional
((zep_ok=0))
if [ -f zep.sql.gz ] 
then 
    status_out "Unzipping zep.sql.gz"
    ! gunzip -vf "zep.sql.gz" >&2 && err_exit "Invalid zep.sql.gz! abort"
    ((zep_ok=1))

    if [ -f zep.tar ]
    then
        status_out "Extracting zep.tar"
        tar -vxf zep.tar 2>/dev/null | awk "$awk_cmd" >&2
        [[ ${PIPESTATUS[0]} -ne 0 ]] && err_exit "Extracting Zeneventserver indexes failed! abort"
    else
        info_out "No Zeneventserver indexes archive, continue"
    fi
else
    info_out "No events archive, continue"
fi

# catalogservice file is optional
if [ -f zencatalogservice.tar ]
then
    status_out "Extracting zencatalogservice.tar"
    tar -vxf zencatalogservice.tar | awk "$awk_cmd" >&2
    [[ ${PIPESTATUS[0]} -ne 0 ]] && err_exit "Extracting zencatalogservice.tar failed! abort"
else
    info_out "No catalogservice archive, continue"
fi

# prep the staging area
! mkdir -p "$staging_zenbackup_dir" && err_exit "Cannot create staging directory in the containter!"

((perf_ok=0))
perf_tarball=""
[[ -f perf.tar && -f perf.tar.gz ]] && err_exit "Multiple perf data tarballs found!"
if [[ -f perf.tar ]]; then
    perf_tarball="perf.tar"
    tar_flags="-vxf"
elif [[ -f perf.tar.gz ]]; then
    perf_tarball="perf.tar.gz"
    tar_flags="-vxzf"
fi
if [[ -n $perf_tarball ]]
then
    # extract the perf into the shared staging volume
    status_out "Extracting $perf_tarball"
    info_out "This operation tends to take a long time ..."
    tar -C "$staging_zenbackup_dir" "$tar_flags" "$perf_tarball" | awk "$awk_cmd" >&2
    [[ ${PIPESTATUS[0]} -ne 0 ]] && err_exit "Extracting performance data from $perf_tarball failed!"
    ((perf_ok=1))
else
    info_out "No performance data archive, continue"
fi

info_out "Setup proper access right"
find . -type d -exec chmod a+rwx {} \; >&2 &
find . -type f -exec chmod a+rw {} \; >&2 &
find "$staging_dir" -type d -exec chmod a+rwx {} \; >&2 &
find "$staging_dir" -type f -exec chmod a+rw {} \; >&2 &
wait

# use the mounted directory as the current directory
# no redirect of stdout where meta data is reported
cmd="cd /mnt/pwd; /opt/zenoss/bin/python /import4/pkg/bin/import4 "
status_out "Finding import meta data"
! su - zenoss -c "$cmd model check"            && err_exit "Model files not valid!"

# optional prevalidation
[ $zep_ok -eq 1 ]  && ! su - zenoss -c "$cmd events check"           && err_exit "Events files not valid!"
[ $perf_ok -eq 1 ] && ! su - zenoss -c "$cmd perf --skip-scan check" && err_exit "Performance data files not valid!"

info_out "Migration files checked OK..."
info_out "No need to commit image for this operation..."
exit 42
