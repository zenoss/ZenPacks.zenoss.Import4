##############################################################################
#
# Copyright (C) Zenoss, Inc. 2014-2015, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################
# these variables must be provided
# metric, device, key, dmduuid
BEGIN {
    # tracking parsing context
    rra=0
    type=0
    cf=0
    avg=0
    db=0
}
{
    if (index($0,"GAUGE") > 0) { type = 0; next } 
    if (index($0,"DERIVE") > 0) { type = 1; next }      # future
    if (index($0,"COUNTER") > 0) { type = 3; next }     # future
    if (index($0,"ABSOLUTE") > 0) { type = 4; next }    # future
    if (index($0,"<rra>") > 0) { rra = 1; next }
    if (index($0,"</rra>") > 0) { rra = 0; avg = 0; db = 0; next }
    if ((rra == 1) && (index($0,"AVERAGE") > 0)) { avg = 1; next }
    if ((avg == 1) && (index($0,"<database>") > 0)) {db = 1; next }
    if (db == 1) {
        if (index($0,"</database>") > 0) {db = 0; next}
        if (index($0,"<v>NaN</v>") > 0) { next }

        tm_idx = match($0, "[0-9]{10}")
        if (tm_idx == 0) { next }
        tm_v = substr($0, tm_idx, 10)

        v_idx = index($0, "<v>")
        if (v_idx == 0) { next }
        v_v = substr($0, v_idx+3, 16)

        print metric, tm_v, v_v, "device=" device, "key=" key, "zenoss_tenant_id=" dmduuid
    }
}
