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

# This script is not a generic xml parser
# It assumes a fixed text layout from the rrdtool (ver:1.4.7-1.el6.rfx) dump command

BEGIN {
    # tracking parsing context
    CONVFMT = "%1.10e"
    rra=0
    type=0
    cf=0
    avg=0
    db=0
    step=1.0
    derived=0.0
    row_fmt="%s %d %.10e device=%s key=%s zenoss_tenant_id=%s\n"
}
{
    # the majarity of the lines
    if (db == 1) {
        if (index($0,"<v>NaN</v>") > 0) { next }
        if (index($0,"</database>") > 0) {db = 0; next}

        tm_idx = match($0, " [0-9]{10} ")
        if (tm_idx == 0) { next }
        tm_v = substr($0, tm_idx+1, 10)

        v_idx = index($0, "<v>")
        if (v_idx == 0) { next }
        vv_idx = index($0, "</v>")
        v_v = substr($0, v_idx+3, vv_idx-v_idx-3)

        if      (type == 0) {
            # GAUGE
            printf row_fmt, metric, tm_v, v_v, device, key, dmduuid
        }
        else if ((type == 1) || (type == 2)) {
            # DERIVED and COUNTER types are proceessed the same way 
            derived += strtonum(v_v)
            _vl = derived*step
            printf row_fmt, metric, tm_v, _vl, device, key, dmduuid
        }
        else if (type == 3) {
            # ABSOLUTE
            _vl = strtonum(v_v)*step
            printf row_fmt, metric, tm_v, _vl, device, key, dmduuid
        }
        next
    }

    if ((i=index($0,"<step>")) > 0) {
        ii=index($0,"</step>")
        # extract step
        step=strtonum(substr($0, i+6, ii-i-6))

        # print "STEP is", step+0 > "/dev/stderr"
        next
    }
    if (index($0,"GAUGE") > 0) { type = 0; next } 
    if (index($0,"DERIVE") > 0) { type = 1; next }
    if (index($0,"COUNTER") > 0) { type = 2; next }
    if (index($0,"ABSOLUTE") > 0) { type = 3; next }
    if (index($0,"<rra>") > 0) { rra = 1; next }
    if (index($0,"</rra>") > 0) { rra = 0; avg = 0; db = 0; next }
    if ((rra == 1) && (index($0,"AVERAGE") > 0)) { avg = 1; next }
    if ((avg == 1) && (index($0,"<database>") > 0)) {db = 1; next }
}
