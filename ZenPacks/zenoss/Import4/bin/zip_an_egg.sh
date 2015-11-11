#!/usr/bin/bash
##############################################################################
#
# Copyright (C) Zenoss, Inc. 2014-2015, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

# a simple script to zip a given dir into an egg under the given directory
egg_path=$1
egg_name=$(basename "$egg_path")

echo $egg_path
echo $egg_name
cd "$egg_path"
zip -r "$egg_name" *
