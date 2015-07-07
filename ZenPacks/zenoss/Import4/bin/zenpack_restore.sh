#!/usr/bin/env bash

restore() {
    orig_actions="/opt/zenoss/var/zenpack_actions.txt_original"
    if [[ ! -f $orig_actions ]]; then
        echo "file $orig_actions does not exist"
        return 1
    fi
    for pack in $(awk '{print substr($1, 2);}' "$orig_actions"); do
        echo "Installing ZenPack $pack"
        zenpack --install "$pack" --ignore-service-install
        if [[ $? != 0 ]]; then
            echo "failed to install zenpack $pack, aborting"
            return 1
        fi 
        echo "Successfully Installed ZenPack $pack"
    done
}

restore
