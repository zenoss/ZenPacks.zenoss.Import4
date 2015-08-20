##############################################################################
#
# Copyright (C) Zenoss, Inc. 2014-2015, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

# common variables
export tsdb_dir="/import4/Q.tsdb"   # the path to keep the final tsdb import files
export task_dir="/import4/Q.tasks"  # the path keeping the unclaimed tasks
export job_dir="/import4/Q.jobs"    # the path keeping the tasks being processed
export imp4_tmp="/import4/tmp"
export rrds_per_task=1

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
    local cpu_idle=$(flock -w 120 "$idle.lock" cat "$idle")
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
  [[ -f "$idle" ]]      && chmod 777 "$idle"        >/dev/null 2>&1
  [[ -f "$idle.lock" ]] && chmod 777 "$idle.lock"   >/dev/null 2>&1


  # initialize the quota 
  local _interval=5
  local _row_per_sec=50000
  local _quota=0
  (( _quota=_interval*_row_per_sec ))
  echo -n "$_quota" >"$idle.quota"

  while true
  do
      iostat -y -c $_interval 1 | awk '/^ +[0-9]+.[0-9]+/{ print int($6) }' > "$idle.tmp"
      (
        flock -w 120 201 || exit 1

        # update the cpu idle percentage
        mv "$idle.tmp" "$idle"

        # replenish the row allowance = 50K per second
        local _interval=5
        local _row_per_sec=50000
        local _quota=0
        (( _quota=_interval*_row_per_sec ))

        local _prev=$(cat "$idle.quota")
        local _qt=0

        if (( _prev < 0 ))
        then
            (( _qt=_quota+_prev ))
        else
            (( _qt=_quota ))
        fi
        echo -n "$_qt" >"$idle.quota"
      ) 201>"$idle.lock" 
  done
} 
export -f poll_idle

check_quota()
{
    local _quota=$(flock -w 120 "$idle.lock" cat "$idle.quota")
    if (( _quota> 0 ))
    then
        return 0
    else
        info_out "No quota: $_quota"
        return 1
    fi
}

check_pile()
{
    local _tc=0
    local _fc=0
    (( _tc=$(ls -f1 "$tsdb_dir" | wc -l) ))
    (( _fc=$(ls -f1 "$tsdb_dir/.fail" | wc -l) ))

    if (( (_tc+_fc) < 200 )) 
    then 
        return 0
    else
        info_out "Wait for importer"
        return 1
    fi
}
export -f check_pile
