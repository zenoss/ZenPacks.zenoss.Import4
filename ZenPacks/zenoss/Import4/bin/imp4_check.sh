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

cd /mnt/pwd

# check if the backup file is available
[[ ! -f "$1" ]] && echo "Migration file not found!" && exit 2

export staging_dir="/import4/staging/zenbackup"
export zbk="zenbackup"
export awk_cmd='{ if (NR%10 == 0) printf "." }'

# extracting known data files from the tar ball
echo -e "\nExtract zenbackup files..."
! tar -vxf "$1"              && echo "Extracting zenbackup failed!"         && exit 2
! tar -zvxf zenbackup_*.tgz  && echo "Extracting zenbackup_*.tgz failed!"   && exit 2

! cd "$zbk" && echo "Invalid zenbackup file!" && exit 2

! gunzip -vf "zep.sql.gz"   && echo "Uncompressing zep.sql failed!"   && exit 2
! gunzip -vf "zodb.sql.gz"  && echo "Uncompressing zodb.sql failed!"  && exit 2

echo -e "\nExtracting ZenPacks.tar..."
tar -vxf ZenPacks.tar | awk "$awk_cmd"
[[ ${PIPESTATUS[0]} -ne 0 ]] && echo "Extracting ZenPack.tar failed!" && exit 2

echo -e "\nExtracting zencatalogservice.tar..."
tar -vxf zencatalogservice.tar | awk "$awk_cmd"
[[ ${PIPESTATUS[0]} -ne 0 ]] && echo "Extracting zencatalogservice.tar failed!" && exit 2

# extract the perf into the shared staging volume
! mkdir -p "$staging_dir"   && echo "Cannot create staging directory in the containter!" && exit 2

echo -e "\nExtracting performance data tends to take a long time..."
tar -C "$staging_dir" -vxf perf.tar | awk "$awk_cmd"
[[ ${PIPESTATUS[0]} -ne 0 ]] && echo "Extracting performance data from perf.tar failed!" && exit 2

echo -e "\nSetup proper access right..."
find . -type d -exec chmod a+rwx {} \;
find . -type f -exec chmod a+rw {} \;

# use the mounted directory as the current directory
cmd="cd /mnt/pwd; /opt/zenoss/bin/python /import4/pkg/bin/import4 -c "
! su - zenoss -c "$cmd model"            && echo "Model files not valid!"            && exit 2
! su - zenoss -c "$cmd events"           && echo "Events files not valid!"           && exit 2
! su - zenoss -c "$cmd perf --skip-scan" && echo "Performance data files not valid!" && exit 2

echo "Migration files checked OK..."
echo "No need to commit image for this operation..."
exit 1
