##############################################################################
#
# Copyright (C) Zenoss, Inc. 2014-2015, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

# clean up the artifacts but leave .fail and pkg dir for debugging purpose
[[ -d /import4/Q.tsdb/.fail ]] && mv /import4/Q.tsdb/.fail /import4/tmp/Q.tsdb.fail

# now remove the larger artifacts
rm -rf /import4/tmp/rrdtool
rm -rf /import4/staging
rm -rf /import4/Q.*
