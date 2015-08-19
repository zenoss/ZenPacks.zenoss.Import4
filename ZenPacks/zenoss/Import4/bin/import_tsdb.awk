##############################################################################
#
# Copyright (C) Zenoss, Inc. 2014-2015, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

# metric, device, key, dmduuid
function check_tsdb()
{
    icnt=0
    _old_line = ""

    # use version cmd to ensure connected
    print "version" |& TSDB_PORT
    while (TSDB_PORT |& getline > 0)
    {
        icnt += 1
        if (index($0, "Built on") != 0)
        {
            tsdb_ok = 1
            break
        }
        else
        {
            if ($0 != _old_line) {
                print "->", $0 > "/dev/stderr"
                print $0 > ERR_LOG
                _old_line = $0
            }
        }
    }
    
    # ignore the 2 status line if succeeded
    icnt -= 2 

    if (tsdb_ok == 0)
    {
        print "Cannot connect to TSDB!" > "/dev/stderr"
        print "Cannot connect to TSDB!" > ERR_LOG
        close (ERR_LOG)
        exit 1
    }
    else
    {
        printf "TSDB OK, Error:%d\n", icnt
    }
}

BEGIN {
    # tracking parsing context
    icnt=0
    tsdb_cmd = "put"
    tsdb_ok=0
    row_no=0

    # open tsdb port, this must be imported in the container
    TSDB_PORT="/inet/tcp/0/127.0.0.1/4242"
    ERR_LOG="/import4/tsdb.err.log"

    check_tsdb()
}
{
    row_no += 1
    print tsdb_cmd, $0 |& TSDB_PORT
}
END {
    # make sure TSDB_PORT is still working
    check_tsdb()

    close (TSDB_PORT)

    if (icnt>0) {
        print "TSDB import", icnt, "errors detected in ", row_no, "records !!" > "/dev/stderr"
        print "TSDB import", icnt, "errors detected in ", row_no, "records !!" > ERR_LOG
        close (ERR_LOG)
        exit 1
    }
    else {
        print "TSDB import successful:", row_no, "records ..."  > "/dev/stderr"
        printf "%d", row_no > "/tmp/quota.used"
        exit 0
    }
}
