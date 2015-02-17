#
# common scrip utilities to be imported by other scripts
#
err_out ()
{
  echo "$1" " ..." >&2
}
export -f err_out

err_exit()
{
  err_out "$1"
  exit 1
}
export -f err_exit

