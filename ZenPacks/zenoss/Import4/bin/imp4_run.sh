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

# if it is a perf import operation, 
# we also try to clean up worker job queue if operation aborted
export options="__OPTIONS__: $*"
export perf_rex='[[:blank:]]*perf([[:blank:]]+.*[[:blank:]]|[[:blank:]]+)import($|[[:blank:]].*)'

do_trap()
{
    echo "imp4_run.sh trapped with $1 running"
    pkill -u zenoss
    [[ "$options" =~ $perf_rex ]] && /import4/pkg/bin/abort_jobs.sh
}
export -f do_trap

# use the mounted directory as the current directory
cmd="cd /mnt/pwd; /opt/zenoss/bin/python /import4/pkg/bin/import4 $*"
su - zenoss -c "$cmd" &
export running_pid="$!"
trap "do_trap $running_pid" SIGTERM SIGINT
wait "$!"
let rc=$?

# restore the config file
cp  -p /tmp/zodb_db_main.conf.sav /opt/zenoss/etc/zodb_db_main.conf

# check to see if we need to commit the image
[[ $rc != 0 ]] && exit $rc

for op in ' -h ' ' --help' 
do
    if [[ "$options" == *"$op"* ]]
    then
        # no need to commit the image for help commands
        exit 1
    fi
done

# commit only when it is for successful 'model import --zenpack'
if [[ "$options" == *" import "* && "$options" == *"model "* && "$options" == *" --zenpack"* ]]; then
    exit 0
fi

echo "No need to commit image for this operation..."
exit 42
