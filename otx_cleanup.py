#!/usr/bin/python
"""OTX Post Import Whitelisting Tool.

Copyright (c) 2017, Nicholas Albright
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
    * Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright
      notice, this list of conditions and the following disclaimer in the
      documentation and/or other materials provided with the distribution.
    * Neither the name of the organization nor the
      names of its contributors may be used to endorse or promote products
      derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL NICHOLAS ALBRIGHT BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


*NOTE*
This product was built out of RE'ing how the process works,
its probably not perfect
*NOTE*

Alienvault's OSSIM Product utilizes Redis for logging OTX pulse data.
From what I can tell, port 6380 is used for this functionality.
DB 0 = IP/CIDR Observables
DB 1 = File Hashes
DB 2 = Domains
DB 99 = Raw Pulse Data.


It appears that when we remove an observable from the DB 0-2 databases, they
are no longer checked by Rhythm - HOWEVER, if you delete the pulse from DB 99
or if it is modified, the IOC's will be reinserted.

The best technique here is to:
. Maintain a flat text file (whitelist) that is used frequently to purge items
such as checkip.dyndns.org
. Query DB99 for pulses last modified >= 90 days ago and store the PULSE ID
. Compare all observables listed in DB 0-2 with Pulse ID's noted above, remove
 those observables.
. Allow for 'manual' removal of observables in case an analyst needs to stop
the bleeding.
. Allow for 'manual' removal of pulses in case someone broke something in
error and it needs to reimport
"""
import sys
import ast
import time
import redis
import argparse

__author__ = 'Nicholas Albright (@nma_io)'
__license__ = 'BSD License 2.0'
__version__ = 0.1


class OTXDB(object):
    """Handling OTX's Datasets."""

    def __init__(self, db_port=6380):
        """
        Initialization.

        :params db_port port used by REDIS OTX (default running on port 6380).
        """
        self.rdb = {}
        for i in (0, 1, 2, 99):
            self.rdb.update({i: redis.Redis(port=db_port, db=i)})

    def _get_index(self, observable):
        """Internal function to get index location."""
        db_index = 2  # Domain/Host be default.
        if '.' not in observable and '/' not in observable:
            db_index = 1  # File hash
        elif observable.replace('.', '').isdigit() or '/' in observable:
            db_index = 0  # IP Address
        return db_index

    def _get_keys(self, observable):
        """Internal funct to get a list of all keys matching an observable."""
        db_index = self._get_index(observable)
        key_array = self.rdb[db_index].keys(observable)
        return key_array

    def query(self, user_query):
        """
        Query Redis Database.

        :params user_query Observable Value to be queried.
        * Note, we will automatically try to identify observable type.

        returns pulses assigned to observable, or empty list.
        """
        db_index = self._get_index(user_query)
        pulses = []
        keylist = self._get_keys(user_query)
        if len(keylist) < 1:
            return pulses
        for item in keylist:
            pulses += list(self.rdb[db_index].smembers(item))
        return pulses

    def remove(self, observable):
        """Remove observable from Redis Database."""
        db_index = self._get_index(observable)
        keylist = self._get_keys(observable)
        for item in keylist:
            self.rdb[db_index].delete(item)
        return (len(keylist), len(self._get_keys(observable)))

    def remove_old_pulses(self, day_delta):
        """Clean up older pulses.

        :params day_delta number of days you want to keep observables.

        """
        db_index = 99
        pulses = self.rdb[db_index].keys('*')
        for pulse in pulses:
            try:
                data = ast.literal_eval(self.rdb[db_index].get(pulse))
                pulse_time = time.mktime(
                    time.strptime(
                        data['modified'].split('.')[0],
                        '%Y-%m-%dT%H:%M:%S')
                )
                if pulse_time >= int(time.time()) - (86400 * int(day_delta)):
                    continue
                for ind in data['indicators']:
                    if len(self._get_keys(ind)) == 1:
                        # Remove if its only in one Pulse.
                        self.remove(ind)
                        # FIX ME: This should have some pulse ID checking
                        # - and should remove from smembers first.
            except Exception as err:
                print err
                pass

    def remove_pulse(self, pulse_id):
        """Remove Pulse from Datastore.

        :params pulse_id is the 24 character hash of the pulse
            (eg: 54d7b04c11d40853d8e13c8f)

        This function is useful if you need to reimport a full pulse
        due to analyst removal error.
        """
        db_index = 99
        self.rdb[db_index].delete('PulseNS:%s' % pulse_id)


def parse_args():
    """Parse Commandline Arguments."""
    opts = argparse.ArgumentParser(description='OTX Whitelisting Application')
    opts.add_argument(
        '-f', '--filename', help='filename containing whitelist')
    opts.add_argument('-p', '--pulse', help='purge pulse ID')
    opts.add_argument(
        '-r', '--removeold', help='Remove pulses older than... ')
    opts.add_argument(
        '-s', '--single', help='observable to whitelist (only one)')
    args = opts.parse_args()
    if not args.single and not args.removeold and not args.pulse and not args.filename:
        opts.print_help()
        sys.exit()
    return args


if __name__ == '__main__':
    args = parse_args()
    otx = OTXDB()
    if args.filename:
        with open(args.filename, 'r') as fh:
            for line in fh:
                otx.remove(line)
    elif args.single:
        print 'Removing Observable: %s' % args.single
        start, end = otx.remove(args.single)
        print 'Removed %s. %s remaining.' % (start, end)
    elif args.pulse:
        otx.remove_pulse(args.pulse)
        print 'Removing Pulse: %s' % args.pulse
        otx.remove_pulse(args.pulse)
    elif args.removeold:
        otx.remove_old_pulses(args.removeold)
    else:
        print 'I do not understand, please use -h if you need help'
