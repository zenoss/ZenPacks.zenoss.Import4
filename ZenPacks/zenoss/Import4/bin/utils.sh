##############################################################################
#
# Copyright (C) Zenoss, Inc. 2014-2015, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

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
