#!/usr/bin/bash
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

# this is supposed to be executed as a root under the tmp/rrdtool dir
tmpdir="$imp4_tmp/rrdtool"
rm -rf "$tmpdir"
mkdir -p "$tmpdir"
cd "$tmpdir"

Prereq="libdbi ruby xorg-x11-fonts-Type1 gettext libpng12 perl-Time-HiRes"
info_out "Installing $Prereq"
status_out "initialize" "Installing prereq packages ..."
/usr/bin/yum install $Prereq -y >> "$imp4_tmp/install.log" 2>&1

let rc=$?
if [ 0 -ne $rc ]
then
    err_exit "ERROR:Prereq yum installation failed: $rc"
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
    info_out "Getting $pkg"
    status_out "initialize" "downloading $pkg ..."
    /usr/bin/wget --quiet $url/$pkg
    let rc=$?
    if [ 0 -ne $rc ]
    then
        err_exit "ERROR: wget error:$rc"
    fi
    info_out "[OK]"
    status_out "initialize" "$pkg downloaded."
done

/usr/bin/yum erase rrdtool -y   >> "$imp4_tmp/install.log" 2>&1

status_out "initialize" "installing $packages ..."
/usr/bin/rpm -Uvh $packages     >> "$imp4_tmp/install.log" 2>&1
let rc=$?
if [ 0 -ne $rc ]
then
    err_exit "ERROR: Installation error:$rc"
fi
info_out "[OK]"
status_out "initialize" "$packages installed."

# drop a dotfile so that we can tell that initialization happened
mkdir -p /var/import4 && touch /var/import4/.initialized
[[ $? = 0 ]] || err_exit "ERROR: creating initialization marker failed"

# rm -rf /tmp/rrdtool
