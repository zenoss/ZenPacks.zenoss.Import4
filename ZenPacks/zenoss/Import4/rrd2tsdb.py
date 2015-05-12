#!/usr/bin/env python
##############################################################################
#
# Copyright (C) Zenoss, Inc. 2014-2015, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

import argparse
import logging
import subprocess
import StringIO
import lxml.etree as ET
from collections import OrderedDict
import re
import os.path
import json
import sys
import traceback
import string

log = logging.getLogger(__name__)
script_path = os.path.dirname(os.path.realpath(__file__))

_ES = OrderedDict(
    E_ID='RRD path does not contain a device ID',
    E_RRD='RRD dump and conversion error',
    E_TSDB='TSDB entry not correct',
    E_XML='Input XML Parsing Error',
    E_STOP='Stop traversing the tree',
    E_SKIP='Skip the current node to the next',
    E_DMD='Cannot obtain the dmd uuid',
    E_LAST='TERMINATOR')


class _Error(Exception):
    def __init__(self, error_tag):
        self.error_tag = error_tag
        self.error_string = _ES[error_tag]

    def __str__(self):
        return ':'.join((self.error_tag, self.error_string))


class ImportRRD():
    def __init__(self, rrdPath, args):
        '''
        rrdPath /mnt/dumptree/Devices/10.10.99.107/os/something_good/abc.rrd
        where   perfPath = /mnt/dumptree/Devices
                self.device = 10.10.99.107
                self.metric = 10.10.99.107/abc
                self.key = Devices/10.10.99.107/os/something_good
        '''
        self.rrdPath = rrdPath
        self.perfPath = args.perfPath
        self.last_timestamp = 0
        self.derived_value = 0
        self.cf = ''
        self.test_mode = args.test_mode
        self.verify_credential = args.verify_credential
        self.entries = 0
        self.verify_points = [None, None, None]
        self.tbl = string.maketrans(' !"#$%&\'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~',
                                    ' -------------.-0123456789-------ABCDEFGHIJKLMNOPQRSTUVWXYZ----_-abcdefghijklmnopqrstuvwxyz----')
        # timeseries timestamp regex
        self.ts_re = re.compile('\d{4}-\d\d-\d\d \d\d:\d\d:\d\d UTC / \d{8,15}')
        # LINUX time regex
        self.tm_re = re.compile('\d{8,15}')
        try:
            self.dmd_uuid = subprocess.check_output(
                script_path + "/bin/get_dmduuid.sh",
                shell=True)
        except:
            raise _Error('E_DMD')

        log.debug(rrdPath)
        if rrdPath.startswith(self.perfPath):
            _f_name = rrdPath[len(self.perfPath):]
        if _f_name[0] == '/':
            _f_name = _f_name[1:]

        if '/' in _f_name:
            self.device = _f_name.split('/', 1)[0]
            log.info("device:%s" % self.device)

            _context, _rrdName = _f_name.rsplit('/', 1)

            # remove '.rrd' postfix
            if _rrdName.endswith('.rrd'):
                _rrdName = _rrdName[:-4]

            # this is the accompanying gauge file for a derive type
            if _rrdName.endswith('_GAUGE'):
                log.info("Processing derived file:%s", self.rrdPath)
                _rrdName = _rrdName[:-6]

            self.metric = "%s/%s" % (self.device, _rrdName)
            log.info("metric:%s" % self.metric)

            self.key = "Devices/%s" % _context
            log.info("key:%s" % self.key)
        else:
            raise _Error('E_ID')

    def _process_timestamp(self, tag_path, content):
        # we keep the timestamp in self.last_timestamp
        if self.ts_re.match(content.strip()):
            _m = self.tm_re.search(content.strip())
            if _m:
                self.last_timestamp = int(_m.group(0))
        return

    def _process_v(self, tag_path, content):
        # filter v with wrong context
        if tag_path != '/rrd/rra/database/row/v':
            return

        # don't output anything except for 'AVERAGE'
        if self.cf != 'AVERAGE':
            return

        # don't output NaN values
        if content.strip() == 'NaN':
            return

        log.debug("v.%s" % content)
        # compute the tsdb data value per type
        if self.type == 'GAUGE':
            _value = float(content.strip())
        elif self.type == 'DERIVE' or self.type == 'COUNTER':
            self.derived_value += float(content.strip())
            _value = self.derived_value * self.step
        elif self.type == 'ABSOLUTE':
            _value = float(content.strip())*self.step
        else:
            log.warning('Unrecognized rrd type:%s' % self.type)

        # output the tsdb import statement
        self.entries += 1

        # output if it is not in the test nor verify mode
        if self.test_mode:
            return

        # if verification mode
        elif self.verify_credential:
            # always keep the last one
            self.verify_points[2] = [self.last_timestamp, _value]
            # if it is the first
            if not self.verify_points[0]:
                self.verify_points[0] = [self.last_timestamp, _value]
            # pick a random one
            if self.entries == 2221:    # 2221 is just a random pick for debuggability
                self.verify_points[1] = [self.last_timestamp, _value]
            return

        # import/conversion mode
        else:
            print '{} {:d} {:.10e} device={} key={} zenoss_tenant_id={}'.format(
                self.metric, self.last_timestamp, _value,
                self.device, self.key.translate(self.tbl), self.dmd_uuid)
            return

    def _find_context_uid(self, context_key):
        '''
        find the context uid of a data source
        TBD - ???
        '''
        return ""

    def _process_a_node(self, tag, tag_path, content):
        # depending on the tag
        # log.debug("Doing: %s, %s" % (tag_path, content))

        # switch on the tags
        if tag is ET.Comment:
            # this content could contain a timestamp
            self._process_timestamp(tag_path, content)
        elif tag == 'type':
            self.type = content.strip()
            log.info("Type:%s" % self.type)

            # type can be GAUGE, COUNTER, DERIVE, ABSOLUTE
            # the values need to be handled differenly
            # if a DERIVE or COUNTER type check accompanying _GAUGE file
            # if so, skip the traversing altogether
            if self.type == 'DERIVE' or self.type == 'COUNTER':
                _gFile = self.rrdPath[:-4] + "_GAUGE.rrd"
                if os.path.isfile(_gFile):
                    log.info("Found GAUGE file, skipping %s" % self.rrdPath)
                    raise _Error('E_STOP')
        elif tag == 'v':
            self._process_v(tag_path, content)
        elif tag == 'cf':
            # note that multiple AVERAGE section
            # may produce out-of-order and dup value
            # results need to be post processed by sort | uniq
            # before feeding to tsdb import
            log.info("cf.%s" % content)
            self.cf = content.strip()
        elif tag == 'step':
            self.step = float(content.strip())
            if self.step <= 0.0:
                raise _Error('E_XML')
        # else
        return

    def _traverse_nodes(self, node, tag_path):
        # recursively process the node based on its tag
        if node.tag is ET.PI:
            my_tag_path = '%s/??' % tag_path
        elif node.tag is ET.Comment:
            my_tag_path = '%s/--' % tag_path
        else:
            my_tag_path = '%s/%s' % (tag_path, node.tag)

        try:
            # log.debug('Found: %s' % my_tag_path)
            self._process_a_node(node.tag, my_tag_path, node.text)
            for child in node:
                self._traverse_nodes(child, '%s' % my_tag_path)
        except _Error as e:
            if e.error_tag != 'E_STOP':
                log.exception(e)
            raise e

    def _do_verify(self, pnt):
        # point is a pair of timestamp(int) and value(float)
        # query tsdb about the tags/metric with a timestamp ..
        # check the returned value
        if not pnt:
            return

        _mtime = pnt[0]
        _mvalue = pnt[1]

        try:
            _json_str = (
                '{'
                '"start":%d,'
                '"end":%d,'
                '"returnset":"last",'
                '"metrics":[{"metric":"%s",'
                '            "aggregator":"avg",'
                '            "tags":{"key":["%s"],'
                '                    "device":["%s"],'
                '                    "zenoss_tenant_id":["%s"]}'
                '        }]}'

            ) % (_mtime-1,
                 _mtime,
                 self.metric,
                 self.key.replace(' ', '-'),
                 self.device,
                 self.dmd_uuid)

            _cmd_str = ('curl -u %s -k -X POST -s '
                        '-H "Content-Type: application/json" '
                        '-d \'%s\' '
                        'http://localhost:8080/api/performance/query') % (
                            self.verify_credential,
                            _json_str)

            log.debug(_cmd_str)
            _result = subprocess.check_output(_cmd_str, shell=True)

            log.debug(_result)
            _json_data = json.loads(_result)
        except Exception as e:
            log.exception(e)
            raise _Error('E_TSDB')

        # verify here, log warning and raise exception
        try:
            _tm = int(_json_data["results"][0]["datapoints"][0]["timestamp"])
            _vl = float(_json_data["results"][0]["datapoints"][0]["value"])

            if _tm != pnt[0]:
                log.warning('Timestamp not matching:%d/%d' % (_tm, pnt[0]))
                raise _Error('E_TSDB')

            # What is the best way to compare two floating points?
            if _mvalue == 0.0:
                _err = _vl
            else:
                _err = abs(1.0 - _vl/_mvalue)

            if _err > 0.0000001:
                log.warning('Value not matching:%f/%f' % (_vl, _mvalue))
                raise _Error('E_TSDB')

        except Exception as e:
            log.exception(e)
            raise _Error('E_TSDB')

        return

    def write_tsdb(self):
        '''
        We assume the size of the rrdfile is limited (e.g. 280KB)
        a direct parsing of the whole xml in memory is OK
        '''
        # convert rrd to xml
        try:
            _cmd = ['rrdtool', 'dump', self.rrdPath]
            _xml_str = subprocess.check_output(_cmd)
        except Exception as e:
            log.exception(e)
            raise _Error('E_RRD')

        try:
            tree = ET.parse(StringIO.StringIO(_xml_str))
            root = tree.getroot()
            tree.docinfo.xml_version
            log.info("xml version=" + tree.docinfo.xml_version)
            log.info("encoding=" + tree.docinfo.encoding)
            log.info(tree.docinfo.doctype)
            self._traverse_nodes(root, '')
        except _Error as e:
            # 'E_STOP' when traverse ends
            if e.error_tag != 'E_STOP':
                log.exception(e)
                raise _Error('E_XML')
        except Exception as e:
            log.exception(e)
            raise _Error('E_XML')

    def verify(self):
        # verify the collected three points against the tsdb
        try:
            self._do_verify(self.verify_points[0])
            self._do_verify(self.verify_points[1])
            self._do_verify(self.verify_points[2])
            log.info('%s verified ...' % self.metric)
        except _Error as e:
            # absorb the exception and continue
            log.info('FAILED:%s' % self.rrdPath)
            if e.error_tag == 'E_TSDB':
                log.warning('Error in verification')
            raise e

        log.info('OK:%s' % self.rrdPath)
        return


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Convert a Zenoss 4.x rrd file \
            into a 5.x opentsdb import file,\n"
            "mapping the data source type to time series"
        )
    )

    parser.add_argument('-l', '--log', choices=['debug', 'info', 'warning'],
                        dest='log_level', default='warning',
                        help="Log tracing output to stderr")
    parser.add_argument('-c', '--config',
                        dest='config_file', default='',
                        help="Configuration file (TBD)")
    parser.add_argument('-w', '--ignore-warnings', action='store_true',
                        dest='ignore_warnings', default=False,
                        help="Continue with the conversion even with warnings")
    parser.add_argument('rrd_files', nargs='+', type=argparse.FileType('r'),
                        help="a list of rrd files (absolute path)")
    parser.add_argument('-p', '--perf',
                        dest='perfPath', default='/import4/staging/perf/Devices',
                        help='The absolute path of the root to device rrd tree\
                        <first level nodes are the device ids>')

    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument('-t', '--test_mode', action='store_true',
                       dest='test_mode', default=False,
                       help="Perform a parse on the input file and generate stat info, only")
    group.add_argument('-v', '--verify_credential',
                       dest='verify_credential', default=None,
                       help=("Perform a validation by sampling/comparing input against tsdb,"
                             "credential must be supplied.. e.g. 'admin:zenoss' "))

    args = parser.parse_args()
    return args


def configLogger(level):
    if level == 'debug':
        _level = logging.DEBUG
    elif level == 'info':
        _level = logging.INFO
    else:
        _level = logging.WARNING

    log.setLevel(_level)
    _ch = logging.StreamHandler()
    _ch.setLevel(_level)
    _fmt = logging.Formatter('%(asctime)s[%(levelname)s] %(message)s')
    _ch.setFormatter(_fmt)
    log.addHandler(_ch)


def main():
    args = parse_args()
    configLogger(args.log_level)

    _total = 0

    try:
        for f in args.rrd_files:
            imp = ImportRRD(f.name, args)
            imp.write_tsdb()
            _total += imp.entries

            # verify per rrd file
            if args.verify_credential:
                imp.verify()

    except _Error as e:
        log.exception(e)
        raise e
    except Exception as e:
        log.exception(e)
        raise e

    if args.test_mode:
        # print the number of records found
        print "%d" % _total

if __name__ == "__main__":
    try:
        main()
    except:
        traceback.print_exc(file=sys.stdout)
        sys.exit(1)

    sys.exit(0)
