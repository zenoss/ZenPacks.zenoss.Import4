##############################################################################
#
# Copyright (C) Zenoss, Inc. 2014-2015, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

export tsdb_dir="/import4/Q.tsdb"   # the path to keep the final tsdb import files
export task_dir="/import4/Q.tasks"  # the path keeping the unclaimed tasks
export job_dir="/import4/Q.jobs"    # the path keeping the tasks being processed
export imp4_tmp="/import4/tmp"
mkdir -p "$imp4_tmp"

#
# common scrip utilities to be imported by other scripts
#
err_out ()
{
  echo -e "[ERROR] $1" " !!" >&2
}
export -f err_out

err_exit()
{
  err_out "$1"
  exit 2
}
export -f err_exit

status_out ()
{
  echo -e "{\"imp4_status\": {\"$1\": \"$2\"}}"
}
export -f status_out

info_out ()
{
  echo -e "[INFO] $1" " ..." >&2
}
export -f info_out

ok_exit()
{
  info_out "$1"
  exit 0
}
export -f ok_exit

export ptag='/import4/staging/perf_importing'
check_monitor()
{
    # check if the perf_import is alive
    flock -n -x "$ptag" echo "Performance import process not started yet"
    if [[ $? -eq 0 ]]
    then
        return 1
    else
        # else, the alive is properly locked by the run command!
        return 0
    fi
}
export -f check_monitor

export idle="/import4/staging/cpu_idle"
check_idle()
{
    cpu_idle=$(flock -w 120 "$idle".lock cat "$idle")
    if [[ $cpu_idle < 10 ]]
    then
        # CPU busy
        info_out "CPU too busy"
        return 1
    else
        info_out "CPU OK"
        return 0
    fi
}
export -f check_idle

poll_idle()
{
  [[ -f "$idle" ]]      && chmod 777 "$idle"
  [[ -f "$idle".lock ]] && chmod 777 "$idle".lock
  while true
  do
      iostat -y -c 2 1 | awk '/^ +[0-9]+.[0-9]+/{ print int($6) }' > "$idle".tmp
      flock -w 120 -x "$idle".lock mv "$idle".tmp "$idle"
  done
} 
export -f poll_idle

check_pile()
{
    if (( $(ls -f1 "$tsdb_dir" | wc -l) < 200 )) 
    then 
        return 0
    else
        info_out "Wait for importer"
        return 1
    fi
}
export -f check_pile
