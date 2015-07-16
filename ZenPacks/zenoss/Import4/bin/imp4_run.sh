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

options="__OPTIONS__: $*"

# bring up the corresponding mysql daemon 
prep_mysqld()
{
    # $1:datadir
    # $2:port
    # reset to the initial content
    rm -rf "$1"/*
    cp -rp /var/lib/mysql/* "$1"

    # start the daemon 
    /usr/bin/mysqld_safe --datadir="$1" --port="$2" --nowatch --socket="$1"/mysql.sock

    # wait until the daemon is running or timeout
    ((i=0))
    while ! /usr/bin/mysqladmin --socket="$1"/mysql.sock status
    do
        echo -n '.'
        sleep 5
        ((i=i+1))
        ((i>12)) && echo -n "\nCannot start mysql daemon!" && exit 1
    done
    echo "Mysql daemon started on $1"
}

# we'll start our own mysqld for import operation if not running
if [[ "$options" == *" import "* && "$options" == *"model "* && "$options" == *" --database"* ]]
then
    prep_mysqld /var/lib/mysql.model 3307
else if [[ "$options" == *" import "* && "$options" == *"events "* && "$options" == *" --database"* ]]
then
    prep_mysqld /var/lib/mysql.events 3306
fi

# use the mounted directory as the current directory
cmd="cd /mnt/pwd; /opt/zenoss/bin/python /import4/pkg/bin/import4 $*"
su - zenoss -c "$cmd"
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
