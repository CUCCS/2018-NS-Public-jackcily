> chap0x08+chap0x09 实战Snort/Suricata检测SQL注入和Shellshock漏洞攻击并联动iptables进行防御（阻断来源IP访问1分钟并记录日志）

- [ ] 实验环境
       ` Victim:     ip 192.168.29.123   Snort/Suricata + Guardian-1.7.tar.gz  + apache2`
       
       `Attacker :   ip 192.168.29.122`
       
- [ ] 实验背景
	- 首先按照[第九章实验](https://sec.cuc.edu.cn/huangwei/textbook/ns/chap0x09/exp.html)方法安装了Snort 和 Guardian-1.7.tar.gz两个工具。
	
		```
		export DEBIAN_FRONTEND=noninteractive# 禁止在apt安装时弹出交互式配置界面
		apt install snort
		 
		wget https://sec.cuc.edu.cn/huangwei/textbook/ns/chap0x09/attach/guardian.tar.gz #下载脚本
		tar zxf guardian.tar.gz  #解压缩
		apt install libperl4-corelibs-perl #安装依赖lib
		编辑 guardian.conf 并保存（修改HostIpAddr为192.168.29.123 和Interface 为eth1
		```
	
	- 安装apache2并开启服务（80端口）

		`apt install apache2 &&service apache2 start`
		
	- 安装Suricata
		```
		apt-get install suricata    #install binary packages in kali(debian)
		
		```
		

	- Shellshock漏洞利用介绍
	
		漏洞原理：利用Apache CGI创建环境变量时的漏洞，将有害代码注入环境变量中，然后利用bash漏洞执行注入的有害代码。
		
		1. `bug1  用户请求可以创建环境变量` 
                Apache CGI处理用户请求信息时，使用了环境变量，在Apache处理headers信息创建环境变量，例如http header中有一个名为ang字段名称，这时CGI会创建一个HTTP_ANG的环境变量，然后传输到服务器的Bash去处理。
		 
		 2. `bug2    bash 区分函数和变量的bug` 
		  bash中，创建函数和创建变量都使用相同的存储方式，二者的区分方式是 bash 函数以 `（）{ ` 开头。所以如果我们在定义环境变量的时候，定义的环境变量以`（）{ ` 开头，bash 程序会将该环境变量当成函数。
		但是如何让函数自动执行呢？
		3. `bug3  自动执行函数体外的代码` 
		当我们在当前的bash shell进程下创建一个bash子进程的时候，新的子进程会读取父进程所有export的环境变量，并复制到自己的进程空间，`在父进程的环境变量被复制到子进程的过程中，函数体外的代码被自动执行了`。
		 
		
		
		
		
- [ ] 实验步骤
	
	- Snort检测SQL注入和Shellshock漏洞攻击并联动iptables进行防御
	
		- 检测原理
		
			通过检测URL中是否包含SQL注入和Shellshcock漏洞利用必须的关键字判断用户是否有SQL注入和Shellshcock漏洞利用的动机。由于shellshock中只会在http header中进行代码注入，所以在检查shellshock时，content的检查范围只设置为http header。
		
		- 添加检测SQL注入的代码和Shellshock的规则：
		

			```python
			vim  /etc/snort/rules/cnss.rules  #打开文件进行编辑
			alert tcp any any -> any 80 (msg: "Error Based SQL Injection Detected-single quoto"; content: "27" ; sid:100000011; ) #检测用户访问的URL中是否含有单引号
			alert tcp any any -> any 80 (msg: "Error Based SQL Injection Detected-double qouto"; content: "22" ; sid:100000012; ) #检测用户访问的URL中是否含有双引号
			alert tcp any any -> any 80 (msg: "AND SQL Injection Detected"; content: "and" ; nocase; sid:100000060; ) #检测用户访问的URL中是否含有 and
			alert tcp any any -> any 80 (msg: "OR SQL Injection Detected"; content: "or" ; nocase; sid:100000061; ) #检测用户访问的URL中是否含有 or
			alert tcp any any -> any 80 (msg: "Order by SQL Injection"; content: "order" ; sid:1000005; ) #检测用户访问的URL中是否含有 order 
			alert tcp any any -> any 80 (msg: "UNION SELECT SQL Injection"; content: "union" ; sid:1000006; ) #检测用户访问的URL中是否含有union语句
			alert tcp any  any -> any 80 (msg:"Possible CVE20146271 BASH Vulnerability Requested (header) ";flow:established,to_server; content:"() {"; http_header; threshold:type limit,track by_src, count 1, seconds 120; sid:2014092401;) #检测用户访问的HTTP请求中  header中是否包含 () { 
			```
			
		- 规则测试
			- SQL注入检测
			
				`cd /root/guardian`
				
				`perl guardian.pl -c guardian.conf  #启动 guardian.pl`
				
				`snort -q -A fast -b -i eth1 -c /etc/snort/snort.conf -l /var/log/snort/ #打开Snort进行抓包`
				
				分别在URL中包含 `" OR AND order union` 等关键字，`guardian`监视窗口中出现警告，截图如下。
				
				![图一](https://github.com/CUCCS/2018-NS-Public-jackcily/raw/ns_chap0x08_0x09_FlippedClassroom/img/1.PNG)
				![图二](https://github.com/CUCCS/2018-NS-Public-jackcily/raw/ns_chap0x08_0x09_FlippedClassroom/img/2.PNG)
			


				查看`/var/log/snort/` 路径下增加了一个 log日志

				但是在触发规则前后，**iptables规则并无变化(没有出现先增加规则，然后规则又被删除的情况)？？？**
			
			- Shellshock漏洞利用检测
				原理:  构造一个 HTTP Header 中包含有可疑字符串`() {` 的数据包，然后观察Snort是否能检查到该可疑字符串。
				
				- 想用 curl 实现，在Attacker中运行如下语句`curl -H "User-Agent: () { (a)=>\' sh -c "echo date"; cat echo" 192.168.29.123  #向服务器发送包含 () { 的数据包`
				
				但是在服务器端的`guardian` 没有任何输出。
				
				我在服务器端打开wireshark进行抓包，的确发现了包含`() {`的文件符合条件的数据包。

				![图三](https://github.com/CUCCS/2018-NS-Public-jackcily/raw/ns_chap0x08_0x09_FlippedClassroom/img/3.jpg)

	
	
				**不知道为什么匹配不上我定义的Snort规则？？？?**

			
		
		
	
		
	- Suricata检测SQL注入和Shellshock漏洞攻击并联动iptables进行防御
	
		- 首先添加用户自定义规则到文件中
		 	```
		 	vim  /etc/suricata/rules/local.rules   #首先打开用于存储的文件
		 	将规则添加到文件中（和Snort相同的规则）
			
			然后修改配置文件，将用户自定义的规则添加到配置文件中
			vim nano /etc/suricata/suricata.yaml
			在 rule-files 中新增加一项  - local.rules   保存退出
			
		 	```

		- 然后修改`guardian` 的配置文件实现与 iptables 联动
			```
			cd /root/guardian
		    vim guardian.conf    #打开配置文件
			
			修改 LogFile 的配置路径为 suricata的日志路径    /var/log/guardian.log
			保存退出
			```
		
		- 规则测试
			测试方法同Snort。
			
			首先打开 suricata
			`suricata  -c /etc/suricata/suricata.yaml -i eth1 -l /var/log/suricata/`
			
			然后打开guardian
			
			在Attacker中使用浏览器访问 Victim，当URL中带有SQL注入关键字 and or order等关键字时，`suricata`中输出如下：
			 ![图四](https://github.com/CUCCS/2018-NS-Public-jackcily/raw/ns_chap0x08_0x09_FlippedClassroom/img/4.PNG)


			使用`curl -H "User-Agent: () { (a)=>\' sh -c "echo date"; cat echo" 192.168.29.123 `访问Victim时，对应规则依然没有生效。
						

- [ ] 实验九思考题
	
	- IDS与防火墙的联动防御方式相比IPS方式防御存在哪些缺陷？是否存在相比较而言的优势？
	
	 	首先明确一下三者的特点
	 	
	 	Firewall： 防火墙是一种协议控制机制，用于流量限制，但没有主动发现恶意流量的能力。
	 	
	 	IDS：入侵检测系统是一个旁路监听设备，没有也不需要跨接在任何链路上，可以根据流量特征检测入侵，但是并不能控制流量。所以需要与Firewalls协作对恶意流量防御。
	 	
	 	IPS：入侵防御系统是相当于具有流量控制能力的IDS，在检测到恶意流量时，可以通过网络协议，直接进行流量控制。
		
		IDS系统在“大规模组合式、分布式入侵”方面，还没有较好的解决办法，误报和漏报现象严重。
		
	 	相比之下，IPS具有检测和防御能力，可以直接在入口处就开始检测，而不是等进到内部网络以后再进行检测，IPS可以在应用层进行检测，弥补了传统的防火墙+IDS方案不能检测更多内容的不足，IPS可以进行更深度的流量检测。
	 	
	 - 配置 Suricata 为 IPS 模式，重复 [实验四](https://sec.cuc.edu.cn/huangwei/textbook/ns/chap0x09/exp.html#%E5%AE%9E%E9%AA%8C%E6%80%9D%E8%80%83%E9%A2%98)  （内容参考自[Setting up IPS/inline for Linux](https://suricata.readthedocs.io/en/latest/setting-up-ipsinline-for-linux.html)
	 	
	 	使用NFQ配置Suricata 为 IPS 模式，首选使用 `suricata --build-info` 检测是否具有对应的工具
	 	
	 	使用 `suricata -c /etc/suricata/suricata.yaml -q 0`  运行Suricata 的IPS模式（使用 0号队列）
	 	
	 	配置 iptables，以发送流量到0号队列中(不指定时默认0号队列），用于suricata 读取。
	 	```
	 	sudo iptables -I INPUT -j NFQUEUE
		sudo iptables -I OUTPUT -j NFQUEUE
	 	```

		使用 `nmap 192.168.29.123 -A -T4 -n -vv` 暴力扫描 Victim。
		
		由于上文中并未观察到`guardian `对iptables的操作，此处无法对比。
	 	
 
 
- [ ] 参考资料

    - [shellshock介绍](https://www.trendmicro.de/cloud-content/us/pdfs/security-intelligence/white-papers/wp-shellshock.pdf)
    - [shellshock 漏洞](https://blog.csdn.net/jingxia2008/article/details/39637085)
    - [snort rule infographic final nobleed](https://snort-org-site.s3.amazonaws.com/production/document_files/files/000/000/116/original/Snort_rule_infographic.pdf?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAIXACIED2SPMSC7GA%2F20181208%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20181208T065204Z&X-Amz-Expires=172800&X-Amz-SignedHeaders=host&X-Amz-Signature=5ede2851253cc4bf2b9798737c8c5be25246678e07912dd501bdefad604a2b58)
    - [Detect SQL Injection Attack using Snort IDS](https://www.hackingarticles.in/detect-sql-injection-attack-using-snort-ids/)
    - [SNORT1#1 Users Manual 2.9.12](http://manual-snort-org.s3-website-us-east-1.amazonaws.com/)
    - [Inside Shellshock: How hackers are using it to exploit systems](https://blog.cloudflare.com/inside-shellshock/)
    - [Suricata User Guide](https://suricata.readthedocs.io/en/suricata-4.1.0/index.html)
    