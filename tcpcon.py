# -*-coding:utf-8 -*-
#! /usr/bin/python3

import logging
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)   # 设置 logger 用于记录错误
from scapy.all import *

dst_ip = "192.168.1.2"
src_ip = "192.168.1.1"
src_port = RandShort()
dst_port=80



tcp_connect_scan_resp = sr1(IP(src=src_ip,dst=dst_ip)/TCP(sport=src_port,dport=dst_port,flags="S"),timeout=10)    #SYN #只接受一个回复的数据包
if(str(type(tcp_connect_scan_resp))=="<type 'NoneType'>"):   #如果无回复就是关闭
	with open("/mnt/share/1.txt", "w") as file:
		file.write ("Closed1")
elif(tcp_connect_scan_resp.haslayer(TCP)):     #如果回复了tcp数据
	if(tcp_connect_scan_resp.getlayer(TCP).flags == 0x12):  #SYN-ACK
		send_rst = sr(IP(dst=dst_ip)/TCP(sport=src_port,dport=dst_port,flags="AR"),timeout=10)   #RST +ACK   sending packets and receiving answers

		with open("/mnt/share/1.txt", "w") as file:
			file.write("Open")
	elif (tcp_connect_scan_resp.getlayer(TCP).flags == 0x14): #RST
		with open("/mnt/share/1.txt", "w") as file:
			file.write ("Closed2")
