##############################################################################
#
# Copyright (C) Zenoss, Inc. 2014-2015, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

# common files
export ptag='/import4/staging/perf_importing'
check_monitor()
{
    # check if the perf_import is alive
    flock -n -E 1 -x "$ptag" echo "Performance import process not started yet"
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
        return 1
    else
        return 0
    fi
}
export -f check_idle

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
