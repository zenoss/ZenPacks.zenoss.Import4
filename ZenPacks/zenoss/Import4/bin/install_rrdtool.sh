#!/usr/bin/bash
##############################################################################
#
# Copyright (C) Zenoss, Inc. 2014-2015, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################


# this is supposed to execute as a root
tmpdir="/import4/tmp/rrdtool"
rm -rf "$tmpdir"
mkdir -p "$tmpdir"
cd "$tmpdir"

Prereq="libdbi ruby xorg-x11-fonts-Type1 gettext libpng12 perl-Time-HiRes"
echo Installing $Prereq
/usr/bin/yum install $Prereq -y

let rc=$?
if [ 0 -ne $rc ]
then
    echo ERROR:Prereq yum installation failed: $rc
    exit 1
fi

processor=$(uname -p)
url='http://pkgs.repoforge.org/rrdtool'
base_name='rrdtool'
version='1.4.7-1.el6.rfx'

packages=""
packages="${packages} perl-${base_name}-${version}.${processor}.rpm"
packages="${packages} ${base_name}-${version}.${processor}.rpm"
packages="${packages} ${base_name}-devel-${version}.${processor}.rpm"
# packages="${packages} python-${base_name}-${version}.${processor}.rpm"


for pkg in ${packages}
do
    echo Getting $pkg
    /usr/bin/wget --quiet $url/$pkg
    let rc=$?
    if [ 0 -ne $rc ]
    then
        echo "ERROR: wget error:$rc"
        exit 1
    fi
    echo -e "\t[OK]"
done

/usr/bin/yum erase rrdtool -y

/usr/bin/rpm -Uvh $packages
let rc=$?
if [ 0 -ne $rc ]
then
    echo "ERROR: Installation error:$rc"
    exit 1
fi
echo -e "\t[OK]"

# rm -rf /tmp/rrdtool
