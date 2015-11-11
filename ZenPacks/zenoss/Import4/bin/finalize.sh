##############################################################################
#
# Copyright (C) Zenoss, Inc. 2014-2015, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

# clean up the artifacts but leave .fail and pkg dir for debugging purpose
save_this()
{
    [[ -d "/import4/$1/$2" ]] && mv "/import4/$1/$2" "/import4/tmp/$1.$2"
}

save_this Q.tsdb .tmp
save_this Q.tsdb .fail

save_this Q.jobs .tmp
save_this Q.jobs .fail
save_this Q.jobs .part

# now that the large artifacts are on the removable drive
# we do not remove these artifacts afterward
# rm -rf /import4/tmp/rrdtool
# rm -rf /import4/staging
# rm -rf /import4/Q.*
