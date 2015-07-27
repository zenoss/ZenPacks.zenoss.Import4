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
# $3: outPath - the dirctory to hold all the tsdb output files

export perfPath="${1%/}"
export rrdPath="$2"
export outPath="$3"

# if this rrdPath as a matching rrdPath_GAUGE.rrd, we skip this file
[[ -f "${rrdPath%.rrd}_GAUGE.rrd" ]] && ok_exit "GAUGE version exists, $rrdPath skipped"

# excluding the legal metric/key letters
ic='[^0-9a-zA-Z-_./]'
tr_pattern='/*'

 cntx=${rrdPath#"$perfPath/"}
 device=${cntx%%$tr_pattern}
export device=${device//$ic/-}

 key=Devices/$(dirname "$cntx")
export key=${key//$ic/-}

 metric=$device/$(basename "$rrdPath" .rrd)
 metric=${metric%_GAUGE}
export metric=${metric//$ic/-}
export dmduuid="$(/import4/pkg/bin/get_dmduuid.sh)"

info_out "perfdata_path=$perfPath"
info_out "rrdfile_path=$rrdPath"
info_out "metric=$metric"
info_out "device=$device"
info_out "key=$key"
info_out "zenoss_tenant_id=$dmduuid"

# now the rrd2tsdb conversion
rrdtool dump "$rrdPath" | awk -v metric="$metric" -v device="$device" -v key="$key" -v dmduuid="$dmduuid" -f "$progdir/convert.awk"
