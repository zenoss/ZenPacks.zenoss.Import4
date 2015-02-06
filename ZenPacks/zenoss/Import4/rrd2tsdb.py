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
# import sys
import subprocess
import StringIO
import lxml.etree as ET
from collections import OrderedDict
import re

log = logging.getLogger(__name__)

_ES = OrderedDict(
    E_ID='RRD path does not contain a device ID',
    E_RRD='RRD dump and conversion error',
    E_XML='Input XML Parsing Error',
    E_STOP='Stop traversing the tree',
    E_DMD='Cannot obtain the dmd uuid',
    E_LAST='TERMINATOR')


class _Error(Exception):
    def __init__(self, error_tag):
        self.error_tag = error_tag
        self.error_string = _ES[error_tag]

    def __str__(self):
        return ':'.join((self.error_tag, self.error_string))


class ImportRRD():
    def __init__(self, rrdPath, perfPath):
        '''
        rrdPath /mnt/dumptree/Devices/10.10.99.107/os/something_good/abc.rrd
        where   perfPath = /mnt/dumptree/Devices
                self.device = 10.10.99.107
                self.metric = 10.10.99.107/abc
                self.key = Devices/10.10.99.107/os/something_good
        '''
        self.rrdPath = rrdPath
        self.perfPath = perfPath
        self.last_timestamp = 0
        # timeseries timestamp regex
        self.ts_re = re.compile('\d{4}-\d\d-\d\d \d\d:\d\d:\d\d UTC / \d{8,15}')
        # LINUX time regex
        self.tm_re = re.compile('\d{8,15}')
        try:
            self.dmd_uuid = subprocess.check_output("./bin/get_dmduuid.sh",
                                                    shell=True)
        except:
            raise _Error('E_DMD')

        log.debug(rrdPath)
        _f_name = rrdPath.lstrip(perfPath)
        if _f_name[0] == '/':
            _f_name = _f_name[1:]

        if '/' in _f_name:
            self.device = _f_name.split('/', 1)[0]
            log.info("device:%s" % self.device)

            _context, _rrdName = _f_name.rsplit('/', 1)
            _rrdName = _rrdName.rsplit('.', 1)[0]
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
                self.last_timestamp = _m.group(0)
        return

    def _process_v(self, tag_path, content):
        # filter v with wrong context
        if tag_path != '/rrd/rra/database/row/v':
            return

        # TBD need to do different calc for different type
        if self.type == 'GAUGE':
            if content.strip() != 'NaN':
                print '%s %s %s device=%s key=%s zenoss_tenant_id=%s' % (
                    self.metric, self.last_timestamp, content.strip(),
                    self.device, self.key, self.dmd_uuid)
        elif self.type == 'COUNTER':
            log.warning("COUNTER NOT HANDLED YET")
            return
        elif self.type == 'DERIVE':
            log.warning("DERIVE NOT HANDLED YET")
            return
            return
        elif self.type == 'ABSOLUTE':
            log.warning("ABSOLUTE NOT HANDLED YET")
            return
        else:
            log.warning('Unrecognized rrd type:%s' % self.type)

    def _process_a_node(self, tag, tag_path, content):
        # depending on the tag
        # log.debug("Doing: %s, %s" % (tag_path, content))

        # switch on the tags
        if tag is ET.Comment:
            # this content could contain a timestamp
            self._process_timestamp(tag_path, content)
        elif tag == 'type':
            # type can be GAUGE, COUNTER, DERIVE, ABSOLUTE
            # the values need to be handled differenly
            self.type = content.strip()
            log.info("Type:%s" % self.type)
        elif tag == 'v':
            self._process_v(tag_path, content)
            log.info("v.%s" % content)
        elif tag == 'cf':
            if content.strip() == 'MAX':
                raise _Error('E_STOP')

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
            log.debug('Found: %s' % my_tag_path)
            self._process_a_node(node.tag, my_tag_path, node.text)
            for child in node:
                self._traverse_nodes(child, '%s' % my_tag_path)
        except _Error as e:
            if e.error_tag != 'E_STOP':
                log.exception(e)
            raise e

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
                        dest='perfPath', default='/mnt/src',
                        help='The absolute path of the root to device rrd tree\
                        <first level nodes are the device ids>')

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

    try:
        for f in args.rrd_files:
            imp = ImportRRD(f.name, args.perfPath)
            imp.write_tsdb()
    except _Error as e:
        log.exception(e)
        raise e
    except Exception as e:
        log.exception(e)
        raise e


if __name__ == "__main__":
    main()
