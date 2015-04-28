#!/usr/bin/bash

# common block
progdir=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
source "$progdir/utils.sh"

zps_dir='/import4/staging/ZenPacks'
[[ -d "$zps_dir" ]]  || err_exit "No zenpack directory found ..."

# for each egg dir, create an egg for it
find /import4/staging/ZenPacks -maxdepth 1 -type d -name "*.egg" -exec $progdir/zip_an_egg.sh {} \; 
# copy it to the .ZenPack dir
find /import4/staging/ZenPacks -type f -name "*.egg" -exec cp -v {} /opt/zenoss/.ZenPacks \; 
