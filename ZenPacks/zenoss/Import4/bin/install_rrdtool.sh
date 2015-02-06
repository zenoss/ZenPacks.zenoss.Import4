#!/usr/bin/bash

rm -rf /tmp/rrdtool
mkdir -p /tmp/rrdtool
cd /tmp/rrdtool

Prereq="libdbi ruby xorg-x11-fonts-Type1 gettext libpng12 perl-Time-HiRes"
echo Installing $Prereq
sudo /usr/bin/yum install $Prereq -y

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

sudo /usr/bin/yum erase rrdtool -y

sudo /usr/bin/rpm -Uvh $packages
let rc=$?
if [ 0 -ne $rc ]
then
    echo "ERROR: Installation error:$rc"
    exit 1
fi
echo -e "\t[OK]"

# rm -rf /tmp/rrdtool
