import os
import subprocess

from ZenPacks.zenoss.Import4.migration import MigrationBase


class Results(object):
    SYSTEM_ERROR = 'EVENTMIGRATION_SYSTEM_ERROR'
    UNTAR_FAIL = 'EVENTMIGRATION_UNTAR_FAILED'
    INVALID = 'EVENTMIGRATION_INVALID'
    WARNING = 'EVENTMIGRATION_WARNING'
    FAILURE = 'EVENTMIGRATION_FAILURE'
    SUCCESS = 'EVENTMIGRATION_SUCCESS'


def init_command_parser(subparsers):
    # add specific arguments for events migration
    events_parser = subparsers.add_parser('events', help='migrate event data')
    return events_parser


class Migration(MigrationBase):
    def __init__(self, args, progressCallback):
        # common setup setup
        super(Migration, self).__init__(args, progressCallback)
        self.zenbackup_dir = os.path.join(self.tempDir, 'zenbackup')
        self.zenbackup_file = ''

    def prevalidate(self):
        # untar the provided zenbackup package
        result = self._untarZenbackup()
        if result is not Results.SUCCESS:
            return result

        # check the untar results
        if not os.path.exists(self.zenbackup_dir):
            return Results.INVALID

        # attempt to find the zep.sql file
        self.zenbackup_file = os.path.join(self.zenbackup_dir, 'zep.sql')
        if not os.path.isfile(self.zenbackup_file):
            self.zenbackup_file = os.path.join(self.zenbackup_dir, 'zep.sql.gz')
            # try another variety
            if not os.path.isfile(self.zenbackup_file):
                return Results.INVALID

        # all files in place
        return Results.SUCCESS

    def wipe(self):
        # this will be done by the import itself
        print 'Wipe is done by the import'
        return

    def doImport(self):
        self._restoreMySqlDb('zodb')
        return

    def reportProgress(self, raw_line):
        # filtering the lines
        _msg = ''
        if raw_line.find('LOCK TABLES') == 0:
            _msg = raw_line
        elif raw_line.find('DROP TABLE') == 0:
            _msg = raw_line
        elif raw_line.find('CREATE TABLE') == 0:
            _msg = raw_line.split('(', 1)[0]
        elif raw_line.find('INSERT INTO ') == 0:
            _msg = raw_line.split('(', 1)[0]
        elif raw_line.find(Results.SUCCESS) == 0:
            _msg = raw_line
        else:
            # throw away the rest
            _msg = None

        if _msg:
            _msg = 'importing events: %s\n' % _msg.rstrip().lstrip()
            super(Migration, self).reportProgress(_msg)

    def postvalidate(self):
        # we assume the db operations are all correct if no error returned
        return Results.SUCCESS

    def _untarZenbackup(self):
        """
        unpack the backup package to sql files
        """
        cmd = 'tar --wildcards-match-slash -C %s -f %s -x %s' % (
            self.tempDir, self.file.name, 'zenbackup/zep.sql\*')
        if os.system(cmd):
            return Results.UNTAR_FAIL
        else:
            return Results.SUCCESS

    def _restoreMySqlDb(self, db):
        """
        Create MySQL database if it doesn't exist.
        """
        mysql_cmd = ['mysql', '-u%s' % self.user]
        mysql_cmd.extend(['--verbose'])
        if self.password:
            mysql_cmd.extend(['--password=%s' % self.password])

        if self.ip and self.ip != 'localhost':
            mysql_cmd.extend(['--host', self.ip])

        # if port and str(port) != '3306':
        #    mysql_cmd.extend(['--port', str(port)])
        # if socket:
        #    mysql_cmd.extend(['--socket', socket])

        mysql_cmd = subprocess.list2cmdline(mysql_cmd)

        cmd = 'echo "create database if not exists %s" | %s' % (db, mysql_cmd)
        if os.system(cmd):
            return Results.SYSTEM_ERROR

        sql_path = self.zenbackup_file
        if sql_path.endswith('.gz'):
            cmd_fmt = "gzip -dc {sql_path}"
        else:
            cmd_fmt = "cat {sql_path}"
        cmd_fmt += " | {mysql_cmd} {db}"
        cmd = cmd_fmt.format(**locals())
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        while True:
            raw_line = proc.stdout.readline()
            if raw_line != '':
                self.reportProgress(raw_line)
            else:
                break
        self.reportProgress(Results.SUCCESS)

        return Results.SUCCESS
