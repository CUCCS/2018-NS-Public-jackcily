#! /usr/bin/python

import logging
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
from scapy.all import *

dst_ip = "192.168.1.2"
src_port = RandShort()
dst_port= 9000
dst_timeout=10

def udp_scan(dst_ip,dst_port,dst_timeout):
	udp_scan_resp = sr1(IP(dst=dst_ip)/UDP(dport=dst_port),timeout=dst_timeout)
	if (str(type(udp_scan_resp))=="<type 'NoneType'>"): #no response
		with open("/mnt/share/1.txt", "w") as file:
			file.write("open|flitered")
	elif (udp_scan_resp.haslayer(UDP)): # response  open
		with open("/mnt/share/1.txt", "w") as file:
				file.write("open")
	elif(udp_scan_resp.haslayer(ICMP)): # response icmp
		if(int(udp_scan_resp.getlayer(ICMP).type)==3 and int(udp_scan_resp.getlayer(ICMP).code)==3):#desination unreachable
			with open("/mnt/share/1.txt", "w") as file:
				file.write("closed")
		elif(int(udp_scan_resp.getlayer(ICMP).type)==3 and int(udp_scan_resp.getlayer(ICMP).code) in [1,2,9,10,13]):#filter
			with open("/mnt/share/1.txt", "w") as file:
				file.write("closed")
	else:
		with open("/mnt/share/1.txt", "w") as file:
			file.write(str(type(udp_scan_resp)))


udp_scan(dst_ip,dst_port,dst_timeout)