#!/usr/bin/env python
##############################################################################
#
# Copyright (C) Zenoss, Inc. 2014-2015, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

# a utility to run a set of operations needed by import process
import os
import sys
import logging
import argparse
import subprocess
import re
import time


conf_file = os.path.join(os.environ['ZENHOME'], 'etc', 'zope.conf')
log = logging.getLogger(__name__)


def _svc_cmd():
    # get the host ip for serviced
    try:
        _host_ips = os.environ['CONTROLPLANE_HOST_IPS']
    except:
        log.error('CONTROLPLANE_HOST_IPS not available')
        sys.exit(1)

    _host_ips_lst = _host_ips.split(', ')
    if not _host_ips_lst:
        log.error('CONTROLPLANE_HOST_IPS:"%s" not available' % _host_ips)
        sys.exit(1)

    _cmd = '/serviced/serviced --endpoint=%s:4979 service ' % _host_ips_lst[0]
    return _cmd


# find the services whoes name containing the substrings in the list
def _find_svcs(inlist):
    log.info('Finding services')

    _list = []
    _output = subprocess.check_output(_svc_cmd() + " list", shell=True).split('\n')

    for _line in _output:
        _rs = re.sub("[\s,]", " ", _line).split()
        if (len(_rs) < 2 or
            _rs[1].lower() == 'serviceid'):
            log.debug('Skipping %s ...' % _line)
            continue

        for _ss in inlist:
            if _rs[0].lower().find(_ss) >= 0:
                _list.append(_rs[1])
                log.debug('found %s ...' % _rs[0])
                break
    return _list


# list all services excluding those names containing the substrings in the list
def _list_svcs_ex(exlist):
    log.info('Listing services')

    _list = []
    _output = subprocess.check_output(_svc_cmd() + " list", shell=True).split('\n')

    for _line in _output:
        _rs = re.sub("[\s,]", " ", _line).split()
        if (len(_rs) < 2 or
            _rs[1].lower() == 'serviceid'):
            log.debug('Skipping %s ...' % _line)
            continue

        _inc = True
        for _ss in exlist:
            if _rs[0].lower().find(_ss) >= 0:
                _inc = False
                break
        if _inc:
            log.debug('found %s ...' % _rs[0])
            _list.append(_rs[1])

    return _list


def _tokens(_line):
    return re.sub("[\s,]", " ", _line).split()


def _is_stopped(slist):
    for svc in slist:
        _line = subprocess.check_output(_svc_cmd() + " status %s | grep %s" % (svc, svc),
                                        shell=True)
        _rs = _tokens(_line)
        log.debug(_rs)

        # ignore wrong services
        if len(_rs) < 3:
            continue

        # ignore parents
        if _rs[2] == '0':
            continue

        if _rs[2] != 'Stopped':
            log.debug('%s not stopped ...' % _rs[0])
            return False
    return True


def _is_running(slist):
    for svc in slist:
        _line = subprocess.check_output(_svc_cmd() + " status %s | grep %s" % (svc, svc),
                                        shell=True)
        _rs = _tokens(_line)
        # ignore wrong services
        if len(_rs) < 3:
            continue

        # ignore parents
        if _rs[2] == '0':
            continue

        if _rs[2] != 'Running':
            log.debug('%s not running ...' % _rs[0])
            return False
    return True


def _stop_svc(id):
    log.info('Stopping %s ...' % id)
    subprocess.call(_svc_cmd() + " stop %s" % id, shell=True)


def _start_svc(svc_name):
    log.info('Staring %s ...' % svc_name)
    subprocess.call(_svc_cmd() + " start %s" % svc_name, shell=True)


# stop all services except the root service, Imp4Mariadb, and mariadb*
def stop_services(args):
    log.info('Stopping services')

    slist = _list_svcs_ex(['mariadb', 'zenoss.resmgr', 'opentsdb', 'hbase', 'hmaster', 'regionserver', 'zookeeper'])
    for svc in slist:
        _stop_svc(svc)

    _time = 0
    while (_time < 600 and
           not _is_stopped(slist)):
        log.debug('Waiting services to stop...')
        _time += 10
        time.sleep(10)

    if _time >= 600:
        log.error('Service stop failed ...')
        sys.exit(1)


# start all services in the control center
def start_all_services(args):
    log.info('Start services')

    slist = _list_svcs_ex([])
    for svc in slist:
        _start_svc(svc)

    _time = 0
    while (_time < 600 and
           not _is_running(slist)):
        log.debug('Waiting services to run...')
        _time += 10
        time.sleep(10)

    if _time >= 600:
        log.error('Service start failed ...')
        sys.exit(1)
    else:
        # wait 30 more seconds
        log.info('Services all started. Wait 30 more seconds ...')
        time.sleep(30)


def start_model_services(args):
    log.info('Start model services')

    slist = _find_svcs(['mariadb', 'redis', 'zenevent', 'rabbitmq', 'zencatalog'])
    for svc in slist:
        _start_svc(svc)

    _time = 0
    while (_time < 600 and
           not _is_running(slist)):
        log.debug('Waiting model services to run...')
        _time += 10
        time.sleep(10)

    if _time >= 600:
        log.error('Service start failed ...')
        sys.exit(1)
    else:
        # wait 30 more seconds
        log.debug('Wait 30 more seconds ...')
        time.sleep(30)


def global_init(args):
    logging.basicConfig(level=getattr(logging, args.log_level.upper()))
    # reset argv so that Zope2.configure won't complaint
    # sys.argv = ['']
    # load_config("configure.zcml", controlplane)


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "A set of independent utilities for the import4 process"
        )
    )
    parser.add_argument('-l', '--log-level', dest='log_level', default='info',
                        help="Specify the logging level - default:info")

    subparsers = parser.add_subparsers(help='Utility commands for import4')

    parser_stop_svcs = subparsers.add_parser('stop_svcs',
                                             help='Stop services')
    parser_stop_svcs.set_defaults(func=stop_services)

    parser_start_svcs = subparsers.add_parser('start_all_svcs',
                                              help='Start services')
    parser_start_svcs.set_defaults(func=start_all_services)

    parser_start_svcs = subparsers.add_parser('start_model_svcs',
                                              help='Start model services')
    parser_start_svcs.set_defaults(func=start_model_services)

    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    global_init(args)
    args.func(args)

if __name__ == "__main__":
    main()
