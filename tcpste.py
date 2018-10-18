#! /usr/bin/python

import logging
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
from scapy.all import *

dst_ip = "192.168.1.2"
src_port = RandShort()
dst_port=80

stealth_scan_resp = sr1(IP(dst=dst_ip)/TCP(sport=src_port,dport=dst_port,flags="S"),timeout=10)
if(str(type(stealth_scan_resp))=="<type 'NoneType'>"):# no responce
	with open("/mnt/share/1.txt", "w") as file:
		file.write ("Filtered1")
elif(stealth_scan_resp.haslayer(TCP)):
	if(stealth_scan_resp.getlayer(TCP).flags == 0x12):  #receive SA  port open
		send_rst = sr(IP(dst=dst_ip)/TCP(sport=src_port,dport=dst_port,flags="R"),timeout=10)  #reply R
		with open("/mnt/share/1.txt", "w") as file:
			file.write("open")
	elif (stealth_scan_resp.getlayer(TCP).flags == 0x14):# receive RA port closed
		with open("/mnt/share/1.txt", "w") as file:
			file.write("closed")
elif(stealth_scan_resp.haslayer(ICMP)):  #receive ICMP and type Destination Unreachable (3)
	if(int(stealth_scan_resp.getlayer(ICMP).type)==3 and int(stealth_scan_resp.getlayer(ICMP).code) in [1,2,3,9,10,13]):
		with open("/mnt/share/1.txt", "w") as file:
			file.write("Filtered2")