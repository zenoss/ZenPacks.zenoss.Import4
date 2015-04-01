#!/bin/bash
# forcefully cleanup all the ongoing tasks/jobs

targets="
tasks
jobs
tsdb
"

for dname in $targets
do
    # remove the residue directories
    rm -rf "/import4/Q.$dname"

    # recreate the struct
    mkdir -p "/import4/Q.$dname/.done"
    chmod -R a+w "/import4/Q.$dname"
done
