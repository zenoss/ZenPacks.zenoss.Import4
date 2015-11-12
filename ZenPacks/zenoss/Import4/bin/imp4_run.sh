#! /usr/bin/env bash
##############################################################################
#
# Copyright (C) Zenoss, Inc. 2014, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

args="$*"
options="__OPTIONS__: $*"
mysql_sock=""

# bring up the corresponding mysql daemon 
prep_mysqld()
{
    # $1:datadir
    # $2:port
    # reset to the initial content
    rm -rf "$1"/*
    cp -rp /var/lib/mysql/* "$1"

    # start the daemon 
    export mysql_sock="$1"/mysql.sock
    /usr/bin/mysqld_safe --datadir="$1" --port="$2" --nowatch --socket="$mysql_sock"

    # wait until the daemon is running or timeout
    ((i=0))
    while ! /usr/bin/mysqladmin --socket="$mysql_sock" status >/dev/null 2>&1
    do
        echo -n '.'
        sleep 20
        ((i=i+1))
        ((i>12)) && echo -en "\nCannot start mysql daemon!" && exit 1
    done
    echo "Mysql daemon started on $1"
}

# per options, preparing the environment before calling import4
prep_env()
{
    # prep the config for the running environment for zencommands (zodb)
    cp  -p /opt/zenoss/etc/zodb_db_main.conf /tmp/zodb_db_main.conf.sav
    cp  -p /opt/zenoss/etc/zodb_db_imp4.conf /opt/zenoss/etc/zodb_db_main.conf

    # 
    # we'll start our own mysqld for import operation if not running
    if [[   "$options" == *" import "* && "$options" == *"model "*  && "$options" == *" --database"* ]]
    then
        prep_mysqld /var/lib/mysql.model 13307
    elif [[ "$options" == *" import "* && "$options" == *"events "* && "$options" == *" --database"* ]]
    then
        prep_mysqld /var/lib/mysql.events 13306
    elif [[ "$options" == *" import"* && "$options" == *"perf "* ]]
    then
        /import4/pkg/bin/prep_perf_import.sh
    fi
}

stop_mysqld()
{
    [[ -n "$mysql_sock" ]] && /usr/bin/mysqladmin --socket="$mysql_sock" shutdown >/dev/null 2>&1
}

# execute the import4 command
exec_import4()
{
    # use the mounted directory as the current directory
    cmd="cd /mnt/pwd; /opt/zenoss/bin/python /import4/pkg/bin/import4 $args"
    su - zenoss -c "$cmd"
    let rc=$?
}

# restore the image after import4 in case docker image got committed
restore_env()
{
    # stop mysqld if running
    stop_mysqld

    # restore the config file
    cp  -p /tmp/zodb_db_main.conf.sav /opt/zenoss/etc/zodb_db_main.conf
}

### the main sequence ###
prep_env
exec_import4
restore_env

exit $rc
