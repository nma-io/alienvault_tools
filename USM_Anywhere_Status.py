#!/usr/bin/python
"""UI Scraper for Alienvault USM Anywhere."""

import sys
import json
import time
import requests

def teams(teamshook, rawmsg):
    """Send message to Teams/Slack/etc."""
    params = {
        'markdown': True,
        'text': rawmsg
    }
    if requests.post(teamshook, data=json.dumps(params)).status_code == 200:
        return True
    return False
        

URL = "alienvault.cloud/api/1.0"
HOST = "" # <- CHANGE ME  Your Subdomain here

## AUTHENTICATION BLOCK FOR ALIENVAULT.

c = requests.get('https://%s.%s/license/terms' % (HOST, URL))
cookies = 'XSRF-TOKEN=' + c.cookies['XSRF-TOKEN'] + "; JSESSIONID=" + c.cookies['JSESSIONID'] + ";"
orig_headers = {'X-XSRF-TOKEN': c.cookies['XSRF-TOKEN'], 'Content-Type': 'application/json;charset=UTF-8', 'Accept': 'application/json, text/plain', 'Cookie': cookies}
loginString = json.dumps({"email": "YourAlienvaultLogin", "password": "YourAlienvaultPassword"})  # <-- CHANGE ME
newToken = requests.post("https://%s.%s/login" %(HOST, URL), data=loginString, headers=orig_headers)


cookies = 'XSRF-TOKEN=' + c.cookies['XSRF-TOKEN'] + "; JSESSIONID=" + newToken.cookies['JSESSIONID'] + ";"
headers = {'X-XSRF-TOKEN': c.cookies['XSRF-TOKEN'], 'Content-Type': 'application/json;charset=UTF-8', 'Cookie': cookies}

hosts = {
    "UUID-FOR-SENSOR-1": "SENSOR1",
    "UUID-FOR-SENSOR-2": "SENSOR2",
    "UUID-FOR-SENSOR-3": "SENSOR3"
}

teamsAlert = "-=- Device Information Report -=-\n\nHostname: %s\n\n" % HOST

# Overall
storage = requests.get("https://%s.%s/stats/storage" % (HOST, URL), headers=headers).json()
teamsAlert += "Monthly Usage to date: %d GB of 1000 GB\n\n" % int(storage["currentMonthOnlineDataConsumed"] / 1e+6)

sensor_info = requests.get("https://%s.%s/sensors" % (HOST, URL), headers=headers).json()

for item in sensor_info:
    teamsAlert += ("{} - Feed Version: {}, System Version: {}, Last Update: {}\n\n".format(
        item["name"], item["currentFeedVersion"], item["systemVersion"],
        time.strftime("%Y-%m-%d %H:%M", time.gmtime(int(item["lastConnectionTime"][:10]))))
    )

for host in hosts:
    try:
        x = requests.get("https://%s.%s/apps/control/system-status/checks?nodeGUID=%s" % (HOST, URL, host), headers=headers).json()
        for h in x:
            for row in x[h]:
                for key in row:
                    if key == "result" and row[key] != "HAPPY":
                        teamsAlert += "%s: %s\n\n" % (hosts[host], row["message"])
                    
        x = requests.get("https://%s.%s/apps/syslog-server/status?sensorId=%s" % (HOST, URL, host), headers=headers).json()
        teamsAlert += "%s Devices reporting to Syslog: %d\n\n" % (hosts[host], len(x[host]["Syslog UDP"]["Received Syslog from the following IPs"].split(", ")))
    except: 
        teamsAlert += "Sensor Down: %s\n\n" % host
teams("APIHOOK", teamsAlert)
