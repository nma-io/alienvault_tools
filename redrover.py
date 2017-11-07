#!/usr/bin/python
"""
RedRover.

I got this idea because I was trying to research an Alienvault alarm
and it had over 1000 events within the correlation - all with Suricata pcaps.
I had to click each event to try and find all of the useful data.
After clicking through about 30 or so events, I saw a twitter post
that contained the words "Red Rover."

So the remainder of the investigation I sang "Red Rover, Red Rover,
Send some actual data on over..."

If you find that you're digging through OSSIM/USM and just want to look
at the data payload, give this a shot.
It will output in "strings" format by default, but you may prefer
hexdump - just add a '-d'

Results are Paged.

This script requires you install hexdump and MySQLdb. On most 
instances, MySQLdb should already be installed.

Example:
    apt-get install python-pip python-dev python-mysqldb; pip install hexdump 
"""
import re
import sys
import pydoc
import string
import hexdump
import argparse
import MySQLdb, MySQLdb.cursors


__author__ = 'Nicholas Albright'
__version__ = 0.1
__requirements__ = 'MySQLdb, hexdump'
CONFIG_FILE = '/etc/ossim/ossim_setup.conf'


def config_parse(conffile):
    """Parse Alienvault Config File to extract DB Credentials."""
    parsed_config = {}
    try:
        config = open(conffile).read().splitlines()
        for line in config:
            if line.startswith('user=') or line.startswith('db_ip=') or line.startswith('pass='):
                k, v = line.split('=', 1)
                parsed_config[k] = v
    except Exception as err:
        sys.exit('Config Parser error: %s' % err)
    return parsed_config


def db_connect(username, password):
    """Connect to Database."""
    conn = MySQLdb.connect(host='127.0.0.1', user=username, passwd=password, db='alienvault')
    return conn


def _optionparse():
    """Argument Parser."""
    opts = argparse.ArgumentParser(description='Redrover')
    opts.add_argument('-d', '--dump', help='Get HEXDUMP formatted results (default is printable strings only)')
    opts.add_argument('alertid', help='Alarm/Alert ID to query for.')
    parsed_args = opts.parse_args()
    return parsed_args


def strings(datastream):
    """Get printable strings."""
    x = ''
    for line in datastream.splitlines():
        line = re.sub('\x00{2,30}', ' ', line)
        if re.search('[%s]{8}' % string.printable, line):
            line = ''.join([i for i in line if (ord(i) in (9, 10) or ord(i) > 31 and ord(i) < 127)])
            x += line.replace('  ', '').replace('\x00', '') + '\n'
    return(x)


def main(event_id, username, password, hexdump_output):
    """Our main codeblock.

    :params event_id = Our Alarm/Event ID from Alienvault
    :params username = database username
    :params password = database password
    :params hexdump_output = print output in "hexdump format" (paged)
    """
    raw_evt_data = ''
    mysql_conn = db_connect(username, password)
    cursor = mysql_conn.cursor()
    cursor.execute('SELECT hex(event_id) FROM backlog_event WHERE backlog_id=unhex("%s")' % event_id)
    each_event_id = cursor.fetchall()
    for row in each_event_id:
        cursor.execute('SELECT data_payload from extra_data where event_id=unhex("%s")' % row[0])
        raw_log = cursor.fetchone()
        raw_evt_data += raw_log[0] + '\n'
    if hexdump_output is True:
        pydoc.pager(hexdump.hexdump(raw_evt_data, result='return'))
    else:
        pydoc.pager(strings(raw_evt_data))


if __name__ == '__main__':
    args = _optionparse()
    event_id = args.alertid
    pc = config_parse(CONFIG_FILE)
    hd = args.dump if args.dump else False
    main(event_id, pc['user'], pc['pass'], hd)

