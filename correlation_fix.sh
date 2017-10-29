#!/bin/bash
# Fix that pesky correlation issue where
# alerts can never be closed/worked. 
# Cron? One off? Depending on your frequency needs
# Nicholas Albright (@nma_io)
HOST=`grep ^db_ip= /etc/ossim/ossim_setup.conf | cut -f 2 -d "=" | sed '/^$/d'`
USER=`grep ^user= /etc/ossim/ossim_setup.conf | cut -f 2 -d "=" | sed '/^$/d'`
PASS=`grep ^pass= /etc/ossim/ossim_setup.conf | cut -f 2 -d "=" | sed '/^$/d'`
DB='alienvault'
now=`date +%s`
calc=$((now - 500))
offset="$(date -d @$calc -u +'%Y-%m-%d %H:%M:%S')"

sshpass -p $PASS mysql --default-character-set=utf8 -A -u $USER -h $HOST $DB -p -e "update alarm set removable=1 where status='open' and removable = 0 and timestamp < '$offset';"
