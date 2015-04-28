#!/usr/bin/bash
# a simple script to zip a given dir into an egg under the given directory
egg_path=$1
egg_name=$(basename "$egg_path")

echo $egg_path
echo $egg_name
cd "$egg_path"
zip -r "$egg_name" *
