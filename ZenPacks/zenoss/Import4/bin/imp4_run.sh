#! /usr/bin/env bash
##############################################################################
#
# Copyright (C) Zenoss, Inc. 2014, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

# Parse the arguments

# temporary line to copy /import4 from development code to the zenpack egg image
cmd="cp -rp /import4/pkg/* /opt/zenoss/ZenPacks/ZenPacks.zenoss.Import4-0.0.9dev-py2.7.egg/ZenPacks/zenoss/Import4"
su - zenoss -c "$cmd"

# trace_opt='-m trace --trace --ignore-module=$(cat /mnt/dos/ignore.lst)'
trace_opt=''

# use the mounted directory as the current directory
cmd="cd /mnt/pwd; /opt/zenoss/bin/python $trace_opt /import4/pkg/bin/import4 $*"
su - zenoss -c "$cmd"
