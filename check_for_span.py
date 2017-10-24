#!/usr/bin/python
"""Tool to quickly monitor for SPAN activity on interfaces."""
import os
import sys
import time
import pcapy # Works with Python2 and Python3. Use apt-get or pip, either way
import socket
import subprocess
import multiprocessing
import logging, logging.handlers
    
__author__ = 'Nicholas Albright'
__version__ = 0.2 # Python3 support added.
logging.basicConfig(format='%(message)s', level=logging.INFO)
log = logging.getLogger(__name__)

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(('8.8.8.8', 0))
MYIP = s.getsockname()[0]


def _pp(ts, pkt):
    if pkt:
        return 1
    else:
        return 0


def monitor(iface, ignoreip, queue):
    """Monitor a given interface."""
    pc = pcapy.open_live(iface, 240, True, 100)
    pc.setfilter('tcp and not host %s' % ignoreip)
    count = 0
    ts = int(time.time())
    while (int(time.time()) - ts) < 10:
        count += pc.dispatch(1, _pp)
    if count > 30:  # 30 packets in 10 seconds, TCP, not including our IP:
        queue.put((iface, True))
    else:
        queue.put((iface, False))


def get_interfaces():
    """Collect Interface data."""
    interface_list = []
    interface_query = subprocess.Popen(
        ['/sbin/ifconfig', '-s'], 
        stdout=subprocess.PIPE).communicate()[0]
    for line in interface_query.splitlines():
        if '1500' not in line:  # Ethernet
            continue
        if line.startswith('tun') or line.startswith('tap') or line.startswith('ppp'):
            continue
        interface_list.append(line.split(' ')[0])
    return interface_list


def main():
    """Run our main loop."""
    response_queue = multiprocessing.Queue()
    procs = []
    ifaces = get_interfaces()
    try:
        for interface in ifaces:
            if __name__ == '__main__':
                log.info('[+] Detected Interface: %s, sniffing...' % interface)
            p = multiprocessing.Process(target=monitor, args=(interface, MYIP, response_queue,))
            procs.append(p)
            p.start()
    except KeyboardInterrupt:
        'Caught Break. Exiting.'
        sys.exit()
    for p in procs:
        p.join()
    all_good = False
    while not response_queue.empty():
        i, v = response_queue.get()
        if __name__ == '__main__':
            print('%s: %s' % (i, str(v)))
        if v:
            all_good = True
    if all_good:
        return True
    return False

if __name__ == '__main__':
    log.info('[=] Nicholas\' Span Port Identification Tool [=]')
    if os.geteuid() != 0:
        sys.exit('[-] Run with root/sudo.')
    main()
