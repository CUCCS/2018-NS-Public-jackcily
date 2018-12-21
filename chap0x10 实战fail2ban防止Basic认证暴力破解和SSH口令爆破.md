>> chap0x10 实战fail2ban防止Basic认证暴力破解和SSH口令爆破
>
>- [ ] 实验背景
>
>  - 实验环境
>    `kali     ip 169.254.227.181` 
>    `物理机 （虚拟网卡 ip ：169.254.227.181)  cmder`
>
>   - Apache2的basic认证
>
>   	基本认证（Basic access authentication）是一种用来允许网页浏览器或其他客户端程序在请求时提供用户名和口令形式的身份凭证的一种登录验证方式。
>
>  - 配置Apache2开启basic认证
>
>    - Apache2一些默认配置路径
>
>      ```
>      apache2 log的默认文件路径 /var/log/apache2
>      apache2 虚拟主机配置文件  /etc/apache2/sites-enabled/000-default.conf
>      apache2 网站默认根目录  /var/www/html/
>      ```
>
>    - 修改Apache2开启basic认证
>
>      ```
>      htpasswd -bc db test 1234  #首先生成用户名和密码
>      cat db #查看生成的用户名密码
>      
>       vim /etc/apache2/sites-enabled/000-default.conf  #打开配置文件
>      	向文件中添加以下内容
>       	 
>      	<Directory "/var/www/html">        #需要保护的文件路径
>      	AuthType Basic                 #认证模式为 basic
>      	AuthName "Restricted Content"  
>      	AuthUserFile /etc/apache2/sites-enabled/db   #设置生成的用户名和密码的路径
>        Require valid-user  #设置可访问的用户
>      	</Directory>
>      	问修改文件保存后，重启Apache2
>      	 service apache2 restart
>      ```
>
>    配置完成以后，在主机浏览器直接访问kali  ip （169.254.227.182），显示如下：
>    ​    ![图一](https://github.com/CUCCS/2018-NS-Public-jackcily/raw/ns_chap0x10_fial2ban/img/1.PNG)
>
>
>  - 配置kali 支持SSH 登录
>
>    - 配置SSH参数
>
>      ```
>      vim /etc/ssh/sshd_config   #打开SSH配置文件
>      
>      修改以下项：
>      PasswordAuthentication yes
>      PermitRootLogin yes
>      ```
>
>    - 启动SSH服务和使用SSH登陆
>
>      ```
>      service ssh start
>      
>      使用SSH登陆kali虚拟机命令如下（主机 cmder中执行)
>      ssh root@ip  -p 22
>      ```
>
>  - 安装fail2ban
>
>     `apt insatll fail2ban` （-v  0.10)
>
>- [ ] 实验内容
>
>  fali2ban通过扫描日志文件阻止ip访问（时间可设定），fail2ban 通过更新防火墙规则，对可疑ip实施特定的action，防止在短时间内攻击者对口令的枚举（暴力破解）。
>
>  - fail2ban防止Basic认证暴力破解
>
>    首先配置fail2ban对Apache2口令的监视
>
>    ```
>    vim  /etc/fail2ban/jail.local #首先打开配置文件
>    在文件中添加以下内容
>    
>    [apache]
>    enabled  = true
>    port     = http,https
>    filter   = apache-auth   #进行认证监听
>    logpath  = /var/log/apache2/error.log  #默认监听路径
>    maxretry = 2     #允许尝试次数
>    findtime = 600
>    
>    sudo systemctl enable fail2ban  #打开fail2ban 
>    sudo systemctl restart fail2ban  #重启fail2ban服务
>    ```
>
>    打开kali中的Apache2服务 `service apache2 start`
>    ​	
>    配置完成后，在主机浏览器中使用 ip访问虚拟机kali,使用错误的用户名密码输入两次以后，无法访问虚拟机kali的Apache服务了，此时查看iptables,可以发现iptables中多了一条`阻止本机进行http访问`的规则,如下：
>
>    ```
>    Chain INPUT (policy ACCEPT)
>    target     prot opt source               destination         
>    f2b-apache  tcp  --  anywhere             anywhere             multiport dports http,https
>    
>    Chain FORWARD (policy ACCEPT)
>    target     prot opt source               destination         
>    
>    Chain OUTPUT (policy ACCEPT)
>    target     prot opt source               destination         
>    
>    Chain f2b-apache (1 references)
>    target     prot opt source               destination         
>    REJECT     all  --  169.254.227.181      anywhere             				reject-with icmp-port-unreachable
>    RETURN     all  --  anywhere             anywhere 
>    ```
>
>    bantime结束以后，查看iptables中f2b-apache的对ip 169.254.227.181 的阻止规则被清除。
>
>  - fail2ban防止SSH口令爆破
>
>    首先配置fail2ban对SSH登录的监视
>
>    ```
>    vim  /etc/fail2ban/jail.local #首先打开配置文件
>    在文件中添加以下内容
>    [sshd]
>    enabled = true
>    banaction = iptables-multiport
>    
>    sudo systemctl enable fail2ban  #打开fail2ban 
>    sudo systemctl restart fail2ban  #重启fail2ban服务
>    ```
>
>    查看fail2ban中SSH相关配置
>    ```
>    vim /etc/fail2ban/jail.conf   #查看配置文件
>    bantime =10m  #默认阻止ip 10分钟
>    findtime = 120   #连续时间 在连续的 findtime 如果失误次数达到 maxretry 就禁止对应ip访问 bantime 的时长
>    maxretry = 5  #允许失误次数	
>    
>    [sshd]
>    #mode   = normal
>    port    = ssh                     #设置fail2ban 监听端口
>    logpath = %(sshd_log)s    #默认监听的logpath
>    backend = %(sshd_backend)s
>    
>    其中 logpath 在 /etc/fail2ban/paths-common.conf 中被赋值为var/log/auth.log
>    ```
>
>    在SSH登录时，尝试输入错误的密码
>    命令行中显示如下：
>      ![图三](https://github.com/CUCCS/2018-NS-Public-jackcily/raw/ns_chap0x10_fial2ban/img/3.PNG)
>
>    从上图中可以看出，在第一次输入密码错误以后，第二次尝试登录时服务器无响应。
>
>    此时查看kali中 iptables ，如下，iptables中多了一条阻止本机SSH登录的规则，主机尝试进行密码正确的SSH登录，无响应：
>
>    ```
>    iptables -L
>    Chain INPUT (policy ACCEPT)
>    target     prot opt source               destination         
>    fail2ban-SSH  tcp  --  anywhere             anywhere             tcp dpt:ssh
>    
>    Chain FORWARD (policy ACCEPT)
>    target     prot opt source               destination         
>    
>    Chain OUTPUT (policy ACCEPT)
>    target     prot opt source               destination         
>    
>    Chain fail2ban-SSH (1 references)
>    target     prot opt source               destination         
>    REJECT     all  --  169.254.227.181      anywhere             reject-with icmp-port-unreachable
>    RETURN     all  --  anywhere             anywhere  
>    ```
>
>    等阻止事件结束，再次查看iptables，如下，此时 iptables中的阻止本机SSH登录的规则已经被清除，主机尝试进行密码正确的SSH登录，成功登录：
>
>    ```
>    
>    Chain INPUT (policy ACCEPT)
>    target     prot opt source               destination         
>    fail2ban-SSH  tcp  --  anywhere             anywhere             tcp dpt:ssh
>    
>    Chain FORWARD (policy ACCEPT)
>    target     prot opt source               destination         
>    
>    Chain OUTPUT (policy ACCEPT)
>    target     prot opt source               destination         
>    
>    Chain fail2ban-SSH (1 references)
>    target     prot opt source               destination         
>    RETURN     all  --  anywhere             anywhere 
>    ```
>
>
>
>
>- [ ] 参考资料
>
>  - [kali linux下开启ssh服务](http://blog.51cto.com/laoyinga/1766340)
>  - [维基百科 HTTP基本认证](https://zh.wikipedia.org/wiki/HTTP%E5%9F%BA%E6%9C%AC%E8%AE%A4%E8%AF%81)
>  - [ssh基本原理，口令登陆和秘钥（免密）登陆](https://blog.csdn.net/yimingsilence/article/details/52161412)
>  - [fail2ban官网手册](https://www.fail2ban.org/wiki/index.php/Main_Page)
>  - [How To Generate and Configure Htpasswd Password In Linux For Apache and Nginx Server?](https://www.poftut.com/generate-and-configure-htpasswd-password-in-linux-for-apache-and-nginx-server/)
>  - [Protecting SSH with Fail2ban](https://www.booleanworld.com/protecting-ssh-fail2ban/)
>  - [How To Protect an Apache Server with Fail2Ban on Ubuntu 14.04](https://www.digitalocean.com/community/tutorials/how-to-protect-an-apache-server-with-fail2ban-on-ubuntu-14-04)
