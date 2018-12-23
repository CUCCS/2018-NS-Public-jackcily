>  chap0x12 实战Bro网络入侵取证

- [ ] 实验背景

  ```
  apt install bro bro-aux  #安装bro
  ```

- [ ] 实验基本环境信息

  - lsb_release -a

    ```python
    No LSB modules are available.
    Distributor ID:	Kali
    Description:	Kali GNU/Linux Rolling
    Release:	kali-rolling
    Codename:	kali-rolling
    ```


  - uname -a 

    ```python
    Linux bogon 4.17.0-kali3-amd64 #1 SMP Debian 4.17.17-1kali1 (2018-08-21) x86_64 GNU/Linux
    ```

  - bro -v

    ```python
    bro version 2.5.5
    ```

- [ ] 实验内容

   - 首先编辑bro配置文件

    	编辑 /etc/bro/site/local.bro，在文件尾追加两行配置代码
    	```python
    	@load frameworks/files/extract-all-files
   ​	@load mytuning.bro  
    	```

   	在 /etc/bro/site/ 创建新文件mytuning.bro，添加以下语句:


   ​	
   	```python
   	redef ignore_checksums = T;    
   	#默认情况下，bro会丢弃没有合格校验和的数据包，所以如果想分析没有经过NIC计算的本地数据包，需要设置忽略校验码。
   	 
   	redef FTP::default_capture_password = T;
   	#ftp.log 中默认不会显示捕获的FTP登录口令,需要自己配置。
   	
   	vim /etc/bro/site/local.bro  #打开文件
   	#取消以下语句注释启用 SMB  analyzer
   	@load policy/protocols/smb
   	
   	```

   - 使用bro自动化分析pacp文件

     首先下载需要使用的pacp数据包
     ```
     wget http://sec.cuc.edu.cn/huangwei/textbook/ns/chap0x12/attack-trace.pcap
     ```

     使用语句分析pcap文件

     ```
     bro -r attack-trace.pcap /etc/bro/site/local.bro
     ```

     语句执行完毕，发现生成以下log文件和一个extract_files目录。

     ```
     total 252
     -rw-r--r-- 1 root root 189103 Dec 22 20:56 attack-trace.pcap
     -rw-r--r-- 1 root root    278 Dec 22 20:56 capture_loss.log
     -rw-r--r-- 1 root root   1194 Dec 22 20:56 conn.log
     -rw-r--r-- 1 root root    470 Dec 22 20:56 dpd.log
     drwxr-xr-x 2 root root   4096 Dec 22 20:56 extract_files
     -rw-r--r-- 1 root root    868 Dec 22 20:56 files.log
     -rw-r--r-- 1 root root    847 Dec 22 20:56 ftp.log
     -rw-r--r-- 1 root root  21817 Dec 22 20:56 loaded_scripts.log
     -rw-r--r-- 1 root root    397 Dec 22 20:56 ntlm.log
     -rw-r--r-- 1 root root    253 Dec 22 20:56 packet_filter.log
     -rw-r--r-- 1 root root    565 Dec 22 20:56 pe.log
     -rw-r--r-- 1 root root    705 Dec 22 20:56 stats.log
     ```

     目录`extract_files`中包含一个文件
     ```python
     extract-1240198114.648099-FTP_DATA-FHUsSu3rWdP07eRE4l
     ```
     将该文件上传到`virustotal`中，发现62个引擎报毒，可判定该文件是攻击者攻击受害者的文件。

     通过阅读`/usr/share/bro/base/files/extract/main.bro`的源码可知文件名最后一个`- 右侧`的字符串`FHUsSu3rWdP07eRE4l`是文件的`fid`。

     使用 `bro-cut`查看files.log文件中相关数据项
     ```python
     grep ^#fields files.log | tr '\t' '\n'  #查看files.log中所有可用列名
     
     bro-cut  ts  fuid tx_hosts rx_hosts conn_uids source mime_type duration  -d < files.log  #按照列名输出一些需要的列
     
     #输出结果如下
     2009-04-19T23:28:34-0400	FHUsSu3rWdP07eRE4l	98.114.205.102	192.150.11.111	Cw8rg33xAwn6mL95M3	FTP_DATA	application/x-dosexec	9.767306
     ```

     由输出结果可知，该文件的来源ip为`98.114.205.102`,该文件的接收方ip是`192.150.11.111`。该文件提取自网络会话标识 `Cw8rg33xAwn6mL95M3`的会话。

     使用bro-cut `查看ftp.log`

     ```python
     bro-cut 	ts uid id.orig_h id.orig_p  id.resp_h id.resp_p user password command arg reply_code reply_msg -d < ftp.log
     
     2009-04-19T23:28:34-0400	CRBjHq8usvPXqm7cb	192.150.11.111	36296	98.114.205.102	8884	1	1	PORT	192,150,11,111,4,56	200	PORT command successful.
     2009-04-19T23:28:34-0400	CRBjHq8usvPXqm7cb	192.150.11.111	36296	98.114.205.102	8884	1	1	RETR	ftp://98.114.205.102/./ssms.exe	150	Opening BINARY mode data connection
     
     ```

     发现被攻击者主机在`2009-04-19T23:28:34-0400` 时刻向攻击者主机请求下载`ssms.exe`的可执行文件。该传输过程发生在网络会话标志为`CRBjHq8usvPXqm7cb`的会话中,其中ftp会话的user和password均为1。

     使用bro-cut `查看conn.log`

     ```
     bro-cut ts uid id.orig_h id.orig_p id.resp_h id.resp_p proto service duration orig_bytes resp_bytes conn_state -d < conn.log
     
     #输出结果如下
     2009-04-19T23:28:28-0400	Cdj2f32BEQjUGvaui	98.114.205.102	1821	192.150.11.111	445	tcp	-	0.238169	0	0	SF
     2009-04-19T23:28:30-0400	CWSyFXuE10p8cjmef	98.114.205.102	1924	192.150.11.111	1957	tcp	-	2.980258	133	2	SF
     2009-04-19T23:28:28-0400	CsHXYgS9c5r9g6xT3	98.114.205.102	1828	192.150.11.111	445	tcp	ntlm	4.938123	4209	902	RSTO
     2009-04-19T23:28:33-0400	CRBjHq8usvPXqm7cb	192.150.11.111	36296	98.114.205.102	8884	tcp	ftp	11.136591	77	214	SF
     2009-04-19T23:28:34-0400	Cw8rg33xAwn6mL95M3	98.114.205.102	2152	192.150.11.111	1080	tcp	ftp-data	9.954513	158720	0	SF
     ```

     其中发现了受害者主机向攻击者主机请求下载`ssms.exe`的会话`CRBjHq8usvPXqm7cb`和有害文件传输的会话`Cw8rg33xAwn6mL95M3`。

     综上可以大致推断攻击者和受害者之间的活动。

     首先攻击者（98.114.205.102）尝试连接受害者（192.150.11.111），并进行漏洞利用，控制受害者电脑执行指令，使受害者向攻击者主动发送ftp下载请求，下载有害文件`ssms.exe`,随后攻击者主机将有害文件通过ftp传输给受害者。

     使用wireshark解析pcap包，发现了攻击者发送给受害者的指令，侧面验证了推断。

     ![图一](https://github.com/CUCCS/2018-NS-Public-jackcily/raw/ns_chap0x12_%E5%AE%9E%E6%88%98Bro%E7%BD%91%E7%BB%9C%E5%85%A5%E4%BE%B5%E5%8F%96%E8%AF%81/img/1.PNG)

     使用bro-cut打开`dpd.log`

     ```
     bro ts uid id.orig_h id.orig_p id.resp_h id.resp_p proto analyzer failure_reason -d < dpd.log
     
     #输出结果如下
     2009-04-19T23:28:29-0400	CsHXYgS9c5r9g6xT3	98.114.205.102	1828	192.150.11.111	445	tcp	SMB	Binpac exception: binpac exception: out_of_bound: SMB1_tree_connect_andx_request:extra_byte_parameters: 60 > 62
     ```

     输出结果中检测到了SMB协议识别。

- [ ] 参考资料

  - [使用bro来完成取证分析](http://sec.cuc.edu.cn/huangwei/textbook/ns/chap0x12/exp.html)
  - [Frequently Asked Questions  ___ Why isn’t Bro producing the logs I expect? (a note about checksums)](https://www.bro.org/documentation/faq.html#why-isn-t-bro-producing-the-logs-i-expect-a-note-about-checksums)
  - [virustotal.com](https://www.virustotal.com/#/home/upload)
  - [Bro 2.5.5 documentation ___  Bro Cluster Architecture](https://www.zeek.org/manual/2.5.5/cluster/index.html)
  - [Challenge 1 of the Forensic Challenge 2010 - pcap attack trace](https://www.honeynet.org/node/504)


​		


​		

​	