#!/bin/bash
# UPDATE_ALL_THE_SCAN_THINGS.sh
# This script can be used to update all of the scan tools when Alienvault fails to do so.

cd /tmp/
echo "Updating GeoIPDB!"
wget http://geolite.maxmind.com/download/geoip/database/GeoLiteCountry/GeoIP.dat.gz >/dev/null 2>&1
wget http://geolite.maxmind.com/download/geoip/database/GeoIPv6.dat.gz >/dev/null 2>&1
wget http://geolite.maxmind.com/download/geoip/database/GeoLiteCity.dat.gz >/dev/null 2>&1
wget http://geolite.maxmind.com/download/geoip/database/GeoLiteCityv6-beta/GeoLiteCityv6.dat.gz >/dev/null 2>&1
wget http://download.maxmind.com/download/geoip/database/asnum/GeoIPASNum.dat.gz >/dev/null 2>&1

for file in $(ls -1 Geo*.dat.gz); do gzip -d $file; done >/dev/null 2>&1
mv Geo*.dat /usr/share/geoip/ >/dev/null 2>&1

echo "Updating OPENVAS!"
openvas-nvt-sync >/dev/null 2>&1

echo "Updating Nikto!"
cd /tmp
apt-get install -y git >/dev/null 2>&1
mv /usr/share/nikto /usr/share/_oldnikto >/dev/null 2>&1
mv /usr/bin/nikto /usr/bin/_oldnikto >/dev/null 2>&1
git clone https://github.com/sullo/nikto  >/dev/null 2>&1
mv /tmp/nikto/program/ /usr/share/nikto/ >/dev/null 2>&1
ln -s /usr/share/nikto/nikto.pl /usr/bin/nikto >/dev/null 2>&1
ln -s /usr/share/nikto/nikto.conf /etc/nikto.conf
echo 'EXECDIR=/usr/share/nikto' >>/etc/nikto.conf

echo "Updating NMAP!"
cd /tmp
mv /usr/share/nmap/scripts /usr/share/nmap/_oldscripts >/dev/null 2>&1
mv /usr/share/nmap/nselib /usr/share/nmap/_oldnselib >/dev/null 2>&1
svn co https://svn.nmap.org/nmap/ >/dev/null 2>&1
cp -R nmap/* /usr/share/nmap/ >/dev/null 2>&1
cd /usr/share/nmap
nmap --script-updatedb  >/dev/null 2>&1
