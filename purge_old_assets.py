#!/usr/bin/python
"""Alienvault Asset Removal Tool - For hosts that haven't been spotted in awhile.

Nicholas Albright 
Copyright, 2017. 
"""
import sys
import socket
import struct
import MySQLdb, MySQLdb.cursors

CONFIG_FILE = '/etc/ossim/ossim_setup.conf'
MYHOSTNAME = socket.gethostname()
REMOVE_OLDER_THAN = 30  # Remove assets older than XX days.
CURSOR = None


def clean_plugins(ipaddr, plugin_file='/etc/ossim/agent/config.yml'):
    """Clean up the OSSIM Plugins Configuration."""
    r = ''
    config_in = open(plugin_file, 'r').read()
    for content in config_in.split('- /'):
        if ipaddr in content:
            continue
        if r:
            r += '- /' + content
        else:
            r += content
    if r:
        config_out = open(plugin_file, 'w')
        config_out.write(r)
        config_out.close()
        return True
    return False


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


def get_assets(remove_days=30):
    """Query Alienvault for all assets that haven't been spotted recently.

    The frequency for the query can be specified using the param: remove_days
    This parameter requires an integer and is checked for safe SQL handling.
    """
    if type(remove_days) != int:
        raise Exception('Error - Get_assets requires an integer.')
    find_asset_sql = 'select hex(id),hex(ctx) from host where external_host = 0 and updated < DATE_SUB(NOW(), INTERVAL %s DAY);' % remove_days
    CURSOR.execute(find_asset_sql)
    r = [(x[0], x[1]) for x in CURSOR.fetchall()]
    return r


def get_asset_ip(asset_hex_id):
    """Query OSSIM-DB for asset IP address."""
    get_ip = 'SELECT hex(ip) from host_ip where host_id = unhex("%s")' % asset_hex_id
    CURSOR.execute(get_ip)
    x = CURSOR.fetchone()
    if not x:
        return False
    return x[0]


def remove_from_ossim_db(host_id, host_ip, ctx_id, human_ip):
    """Remove Assets from OSSIM-DB."""
    remove_sql = [
        'UPDATE hids_agents SET host_id = NULL WHERE host_id = UNHEX("{host_id}");',
        'DELETE FROM host_scan WHERE host_id = UNHEX("{host_id}");',
        'DELETE FROM host_software WHERE host_id = UNHEX("{host_id}");',
        'DELETE FROM host_services WHERE host_id = UNHEX("{host_id}");',
        'DELETE FROM host_properties WHERE host_id = UNHEX("{host_id}");',
        'DELETE FROM host_types WHERE host_id = UNHEX("{host_id}");',
        'DELETE FROM host_sensor_reference WHERE host_id = UNHEX("{host_id}");',
        'DELETE FROM host_ip WHERE host_id = UNHEX("{host_id}");',
        'DELETE FROM host_plugin_sid WHERE host_ip IN (UNHEX("{host_ip}")) AND ctx = UNHEX("{ctx}");',
        'DELETE FROM bp_member_status WHERE member_id = UNHEX("{host_id}");',
        'DELETE FROM bp_asset_member WHERE member = UNHEX("{host_id}") AND type = "host";',
        'DELETE FROM host_vulnerability WHERE host_id = UNHEX("{host_id}");',
        'DELETE FROM host_qualification WHERE host_id = UNHEX("{host_id}");',
        'DELETE FROM host_group_reference WHERE host_id = UNHEX("{host_id}");',
        'DELETE FROM host WHERE id = UNHEX("{host_id}");',
        'DELETE FROM vuln_nessus_latest_reports WHERE hostIP IN ("{human_ip}");',
        'DELETE FROM vuln_nessus_latest_results WHERE hostIP IN ("{human_ip}");'
    ]
    for row in remove_sql:
        CURSOR.execute(row.format(host_id=host_id, ctx=ctx_id, host_ip=host_ip, human_ip=human_ip))


if __name__ == '__main__':
    if len(sys.argv) == 2:
        REMOVE_OLDER_THAN = int(sys.argv[1])
    pc = config_parse(CONFIG_FILE)
    mysql_conn = db_connect(pc['user'], pc['pass'])
    CURSOR = mysql_conn.cursor()
    asset_hexids = get_assets(REMOVE_OLDER_THAN)
    print('%s assets identifed.' % len(asset_hexids))
    # raw_input('Press any key to continue...')
    for row in asset_hexids:
        asset_id, ctx = row
        print('Removing: %s...' % asset_id)
        hexip = get_asset_ip(asset_id)
        if not hexip:
            human_ip = 'BROKEN_LINK_BAD_DB_ENTRY'
            hexip = '00'
        else:
            human_ip = socket.inet_ntoa(struct.pack('!L', int(hexip, 16)))
        remove_from_ossim_db(asset_id, hexip, ctx, human_ip)
    mysql_conn.commit()
