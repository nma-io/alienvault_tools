#!/usr/bin/python
"""Daily System Status Check Script."""
import sys
import MySQLdb, MySQLdb.cursors
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


if __name__ == '__main__':
    pc = config_parse(CONFIG_FILE)
    mysql_conn = MySQLdb.connect(host='127.0.0.1', user=pc['user'], passwd=pc['pass'], db='alienvault')
    CURSOR = mysql_conn.cursor()
    CURSOR.execute('select sum(stat) from acl_entities_stats;'
    eps = int(CURSOR.fetchone()[0])
    print(eps)
