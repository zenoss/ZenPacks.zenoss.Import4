#!/bin/bash
##############################################################################
#
# Copyright (C) Zenoss, Inc. 2014-2015, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

# common block
progdir=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
source "$progdir/utils.sh"

# rrdPath /mnt/dumptree/Devices/10.10.99.107/os/something_good/abc.rrd
# where:    perfPath = /mnt/dumptree/Devices
#           device = 10.10.99.107
#           metric = 10.10.99.107/abc
#           key = Devices/10.10.99.107/os/something_good

# $1: perfPath- /mnt/dumptree/Devices
# $2: rrdPath - /mnt/dumptree/Devices/10.10.99.107/os/something_good/abc.rrd

export perfPath="${1%/}"
export rrdPath="$2"

# if this rrdPath has a matching rrdPath_GAUGE.rrd, we skip this file
[[ -f "${rrdPath%.rrd}_GAUGE.rrd" ]] && ok_exit "GAUGE version exists, $rrdPath skipped"

# excluding the legal metric/key letters
ic='[^0-9a-zA-Z-_./]'
tr_pattern='/*'

 cntx=${rrdPath#"$perfPath/"}
 device=${cntx%%$tr_pattern}
export device=${device//$ic/-}

# find the dev key that the rrdPath mapped to
            devPath=$(dirname "$cntx")   # e.g. 10.10.99.107/os/something_good
  export    key="Devices/$devPath"
            mapped=$(grep "^${key}|" $rrdmap | sed 's/.*|//')
  if [[ ! -z $mapped ]]
  then
      info_out "$devPath mapped to $mapped"
      dev_pattern='*devices/'
      mapped_key="Devices/${mapped#$dev_pattern}"
      if [[ "Devices/${devPath}" != "${mapped_key}" ]]
      then
          info_out "Replacing $devPath with $mapped_key"
          export key=${mapped_key}
      fi
  fi

# cleanup the illegal chars
export key=${key//$ic/-}

 metric=$device/$(basename "$rrdPath" .rrd)
 metric=${metric%_GAUGE}
export metric=${metric//$ic/-}
export dmduuid="$(/import4/pkg/bin/get_dmduuid.sh)"

# worker log 
# info_out "perfdata_path=$perfPath"
# info_out "zenoss_tenant_id=$dmduuid"
# info_out "rrdfile_path=$rrdPath metric=$metric device=$device key=$key"

# now the rrd2tsdb conversion
rrdtool dump "$rrdPath" | awk -v metric="$metric" -v device="$device" -v key="$key" -v dmduuid="$dmduuid" -f "$progdir/convert.awk"
