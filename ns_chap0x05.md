>  实验5        自己动手编程实现并讲解TCP connect scan/TCP stealth scan/TCP XMAS scan/UDP scan


**实验工具**

- scapy     version 2.4.0
- ipython   version 5.5.0
- netcat    version  1.10-41.1

**实验背景**
- [ ]  实验中可能用到的指令
  *  使用netcat监听`tcp：80`端口
         `nc -nvlp 80`
  * 使用netcat监听`udp ：9000`端口，并回复payload为  hello的udp数据包
   ` echo  -n "hello " | nc -nvulp  9000`
   *  在kali scapy 中运行python源码
    `    run   filepath`
    * nmap 扫描  tcp服务
      `nmap  ip`
    * nmap 扫描udp服务某端口
     `nmap -sU ip - p 端口号 `
- [ ]  实验中四种  scan 扫描源码  （转自[此处](https://resources.infosecinstitute.com/port-scanning-using-scapy/)，二次加工）

   - TCP connect scan  source code

```python

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

```

-  TCP stealth scan

```python

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
```
- TCP XMAS scan

```python

#! /usr/bin/python

import logging
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
from scapy.all import *

dst_ip = "192.168.1.2"
src_port = RandShort()
dst_port=80

xmas_scan_resp = sr1(IP(dst=dst_ip)/TCP(dport=dst_port,flags="FPU"),timeout=10)
if (str(type(xmas_scan_resp))=="<type 'NoneType'>"):
	with open("/mnt/share/1.txt", "w") as file:
		file.write("Open|Filtered")
elif(xmas_scan_resp.haslayer(TCP)):
	if(xmas_scan_resp.getlayer(TCP).flags == 0x14):
		with open("/mnt/share/1.txt", "w") as file:
			file.write("Closed")
elif(xmas_scan_resp.haslayer(ICMP)):
	if(int(xmas_scan_resp.getlayer(ICMP).type)==3 and int(xmas_scan_resp.getlayer(ICMP).code) in [1,2,3,9,10,13]):
		with open("/mnt/share/1.txt", "w") as file:
			file.write("Filtered")

```

- UDP scan

```python
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
```




- [ ]  使用 python socket 编程临时开启 udp server，源码如下:
```python
from socket import *
from time import ctime

host = ''
port = 9000
bufsize = 1024
addr = (host,port)

udpServer = socket(AF_INET,SOCK_DGRAM)
udpServer.bind(addr)

while True:
	#print('Waiting for connection...')
	data,addr = udpServer.recvfrom(bufsize)
	data  = data.decode(encoding='utf-8').upper()
	#data = "at %s :%s"%(ctime(),data)
	#print('recv', data)
	udpServer.sendto(data.encode(encoding='utf-8'),addr)
	break
udpServer.close()
print("yes")

```


**实验内容**
实验拓扑图结构如下：（沿用实验一配置）

![tuopu](https://raw.githubusercontent.com/CUCCS/2018-NS-Public-jackcily/ns_chap0x01/8-2.png)


实验内容及结果如下：

- [ ]  使用nc + scapy 测试四种扫描
   其中开启  `tcp:80` 服务使用 `nc -nvlp 80`  
   开启`udp:9000`服务使用 ` echo  -n "hello " | nc -nvulp  9000`
   四种 scan 均为在kali 终端 scapy中运行上文中的脚本
   

|| 扫描类型 |  扫描源|  被扫描者  |  被扫描者提供的服务及端口  |  扫描源获取的扫描结果 |
|--|--|--|--| --|--|
|| TCP connect scan | 网关 | 靶机 | 无 | closed2  (RST)|
|| TCP connect scan | 网关 | 靶机 | tcp:80 |  open (SYN-ACK) |
|  |TCP connect scan |  攻击者 | 靶机 | 无 | closed1 (no response) |
| |TCP connect scan | 攻击者 | 靶机 | tcp:80 | closed1 (no response)|
|  | |  |  |  | |
|  |TCP stealth scan |  网关 | 靶机 | 无 | closed |
|  | TCP stealth scan|  网关 | 靶机 | tcp:80 |open |
|  |TCP stealth scan |  攻击者 | 靶机 | 无 | filter1 (no response)|
|  |TCP stealth scan |  攻击者 | 靶机 | tcp:80 | filter1 (no response)|
|  | |  |  |  | |
|  |TCP XMAS scan |  网关 | 靶机 | 无 | closed|
|  |TCP XMAS scan |  网关 | 靶机 | tcp:80 |open/filtered  (no response)|
|  | TCP XMAS scan| 攻击者 | 靶机 | 无 | open/filtered  (no response)|
|  | TCP XMAS scan|  攻击者 | 靶机 | tcp:80 | open/filtered  (no response)|
|  | |  |  |  | |
|  | UDP scan|网关 | 靶机 | 无 | open/filtered  (no response)|
|  | UDP scan| 网关 | 靶机 | udp:9000 | open |
|  | UDP scan|  攻击者 | 靶机 | 无 | open/filtered  (no response)|
|  | UDP scan| 攻击者 | 靶机 | udp:9000 | open/filtered  (no response)|

   
 实验完成结果和给定的[查阅资料](https://resources.infosecinstitute.com/port-scanning-using-scapy/)基本符合。
 其中，当攻击者试图扫描靶机时，由于数据包根本无法到达靶机，所以攻击者对靶机的端口扫描都是无响应的。
 



- [ ] 使用socket 编程开启udp:9000服务，并用 nmap测试结果
扫描者 ：`网关`       指令   `nmap -sU 192.168.1.2  - p 9000 `
被扫描者：`靶机`    指令   `run  /mnt/share/udpserver.py`
扫描者扫描结果

```
root@bogon:~# nmap -sU 192.168.1.2 -p 9000
Starting Nmap 7.70 ( https://nmap.org ) at 2018-10-18 12:01 EDT
Nmap scan report for localhost (192.168.1.2)
Host is up (0.00024s latency).

PORT     STATE SERVICE
9000/udp open  cslistener
MAC Address: 08:00:27:3C:0F:56 (Oracle VirtualBox virtual NIC)

Nmap done: 1 IP address (1 host up) scanned in 0.13 seconds


```

截图如下：
![pic](https://github.com/CUCCS/2018-NS-Public-jackcily/raw/ns_chap0x05/2.PNG)

参考资料

-   [scapy  scan source code](https://resources.infosecinstitute.com/port-scanning-using-scapy/)
-  [nc](https://akaljed.wordpress.com/2010/12/12/scapy-as-webserver/)
-  [udp  socket  source code](https://blog.csdn.net/chao56789/article/details/81162288)
-  [iptables1](https://wiki.debian.org/iptables)      、     [iptables2](http://mrdede.com/?p=1174)
-  [nc manul](https://linux.die.net/man/1/nc)
-  [service](https://ubuntuforums.org/showthread.php?t=1878232)
-  [nmap](http://einverne.github.io/post/2017/01/nmap.html)
- [tcp flag key](http://rapid.web.unc.edu/resources/tcp-flag-key/)