实验二  # 无线接入网监听

**实验工具**

```
Aircrack-ng + wireshark
```

**实验背景**

1、802.11数据帧主要被分为 管理帧、控制帧、数据帧三大类型。
以下是本实验可能使用的帧以及对应的子类型


| 子类型Subtype值 |  代表的类型 |
|--|--|
| 0x00 | Association Request(关联请求) |
| 0x01 | Association Response (关联响应) |
| 0x02 |  Reassociation Request(重关联请求) |
| 0x03 | Reassociation Response(重关联响应) |
| 0x04 | Probe Request(探测请求) |
| 0x08 |  Beacon(信标帧)|
|  0x09| ATIM(通知传输指示信息) |
| 0x0a |  Disassociation(解除关联)|
| 0x0b |  Authentication(身份验证)|
|0x0c  |  Deauthentication(解除身份验证)|


  
  
2、STA加入一个无线网络时的开放式认证和关联加入网络的步骤如下：



  

      1.扫描阶段（SCAN）
      2.认证阶段 (Authentication) 
      3.关联（Association） 
      


接入过程如下图所示（转载自[此处](https://blog.csdn.net/hmxz2nn/article/details/79937344)）：


![p1](https://github.com/CUCCS/2018-NS-Public-jackcily/raw/mis_chapt0x02/p1.png)



其中无线扫描阶段，STA 有两种方式可以获取周围的无线网络信息。


    被动扫描   (接收周围开启SSID广播的AP的Beacon frame)
    
    主动扫描   (主动向AP发送Probe Request frame, 通过接收AP回复的Probe Response frame获取目标AP的无线网络信息)
               包括客户端发送广播探测请求帧（SSID为空）、客户端发送单播帧（携带指定的SSID）两种数据帧发送方式。




**实验内容**

首先 `airmon-ng check kill` 结束进程

载入网卡监听模式 `airmon-ng start wlan0` ,电脑会自动创建一个 wlan0mon的监听模式接口

查看无线网卡可监听的channel `iwlist  wlanmon channel` 

输出结果如下：

```
wlan0mon  13 channels in total; available frequencies :
          Channel 01 : 2.412 GHz
          Channel 02 : 2.417 GHz
          Channel 03 : 2.422 GHz
          Channel 04 : 2.427 GHz
          Channel 05 : 2.432 GHz
          Channel 06 : 2.437 GHz
          Channel 07 : 2.442 GHz
          Channel 08 : 2.447 GHz
          Channel 09 : 2.452 GHz
          Channel 10 : 2.457 GHz
          Channel 11 : 2.462 GHz
          Channel 12 : 2.467 GHz
          Channel 13 : 2.472 GHz

```



**问题**
1、查看统计当前信号覆盖范围内一共有多少独立的SSID？其中是否包括隐藏SSID？哪些无线热点是加密/非加密的？加密方式是否可知？

在终端中运行  `airodump-ng wlan0mon -w saved`  进行抓包

其中终端显示如下：

```


 CH  2 ][ Elapsed: 36 s ][ 2018-10-04 11:01 ][ realtime sorting activated                                     
                                                                                                              
 BSSID              PWR  Beacons    #Data, #/s  CH  MB   ENC  CIPHER AUTH ESSID
                                                                                                              
 74:C3:30:72:B5:7A  -52       75        1    0  13  270  WPA2 CCMP   PSK  <length:  0>                        
 BC:46:99:38:C7:2E  -88       55        3    0   1  405  WPA2 CCMP   PSK  TP-LINK_C72E                        
 C8:3A:35:38:91:60  -95       51        0    0   3  130  WPA2 CCMP   PSK  峰园汽贸                            
 C8:3A:35:0B:96:F8  -97       71        2    0   6  130  WPA2 CCMP   PSK  Tenda_0B96F8                        
 34:96:72:4A:A3:C4  -97        8        0    0   1  405  WPA2 CCMP   PSK  TP-LINK_A3C4                        
                                                                                                              
 BSSID              STATION            PWR   Rate    Lost    Frames  Probe                                    
                                                                                                               
 74:C3:30:72:B5:7A  54:8C:A0:34:C3:EB  -47    0 - 1      0        4  fastxu                                    
 74:C3:30:72:B5:7A  B4:CD:27:96:77:70  -53    0 - 6      0        1                                            
 BC:46:99:38:C7:2E  1C:48:CE:FA:92:E9   -1    1e- 0      0        3     

```

由终端显示结果可知当前信号覆盖范围内一共有5个独立的SSID，其中有只一个的 ESSID 长度为0，可知只有一个隐藏SSID。

观察下面的工作站列表可知，MAC地址为  `54:8C:A0:34:C3:EB` 的station  接入点的 MAC地址正是 `74:C3:30:72:B5:7A` ，和隐藏SSID的 MAC地址完全相同，由此可以判断该station连接的AP 对应的 `Probe`正是隐藏的SSID。

由此可以判断只要具有一个能正常接入隐藏SSID的station，就能用无线网卡获取到该隐藏SSID，可见单纯的隐藏SSID，并不安全。


由终端中 `ENC` 列和 `CIPHER` 列可知捕获到的5个SSID均使用了WPA2的安全策略和CCMP 的数据加密方式。

抓包结果保存在saved .cap 文件中，共5548bytes，49个数据包。截图如下：
![p5](https://github.com/CUCCS/2018-NS-Public-jackcily/raw/mis_chapt0x02/p5.PNG)

使用 `wlan.fc.sub_type ==0x08` 过滤出 Beacon frame，截图如下：

![p6](https://github.com/CUCCS/2018-NS-Public-jackcily/raw/mis_chapt0x02/p6.PNG)

查看 `SSID == Wildcard`这一条，即终端中SSID length为0的隐藏SSID，验证该数据包的  `Source address` 为`74:C3:30:72:B5:7A`，和隐藏SSID的MAC地址相同，查看该 `Beacon frame` 的`SSID`字段，发现被`0x00`填充。

截图如下：


![p7](https://github.com/CUCCS/2018-NS-Public-jackcily/raw/mis_chapt0x02/p7.PNG)


   要查看该SSID是否需要加密，首先查看 对应的Beacon frame 的 `fixed parameters-Capabilities Information-Privacy 字段`是0还是1 ，若Privacy字段值为1表示为启用加密,则说明AP为加密模式。
   
   
![p8](https://github.com/CUCCS/2018-NS-Public-jackcily/raw/mis_chapt0x02/p8.PNG)
   
  再查看Authentication帧中的Authentication Algorithm字段的值为Open System，则说明并非Shared加密模式，而是Open加密或WPA加密。
  

![p9](https://github.com/CUCCS/2018-NS-Public-jackcily/raw/mis_chapt0x02/p9.PNG)


2、如何分析出一个指定手机在抓包时间窗口内在手机端的无线网络列表可以看到哪些SSID？这台手机尝试连接了哪些SSID？最终加入了哪些SSID？
       
   - 通过查看当前无线网络覆盖范围内有多少Beacon frame，或者回复给该手机的Probe  Responce frame 中的SSID，可知该手机总共可以看到的SSID。
      

 - 通过查看该手机发送的 authentication frame，可以看到该手机试图连接了哪些SSID
 
 
  -  通过检查该手机收到的Association Response帧可以判断该手机最终加入了哪些SSID


以自己的手机接入AP为例演示：
首先在终端输入 `airodump-ng wlan0mon`

终端输出结果如下：

```

 CH  6 ][ Elapsed: 6 s ][ 2018-10-04 22:07                                         
                                                                                                                                
 BSSID              PWR  Beacons    #Data, #/s  CH  MB   ENC  CIPHER AUTH ESSID
                                                                                                                                
 74:C3:30:72:B5:7A  -42       32        0    0  13  270  WPA2 CCMP   PSK  <length:  0>                                          
 A4:93:3F:64:B1:98  -49       36        0    0   6   65  WPA2 CCMP   PSK  233                                                   
 C8:3A:35:38:91:60  -97        7        0    0   9  130  WPA2 CCMP   PSK  峰园汽贸                                              
 BC:46:99:38:C7:2E  -97        8        0    0   1  405  WPA2 CCMP   PSK  TP-LINK_C72E                                          
                                                                                                                                
 BSSID              STATION            PWR   Rate    Lost    Frames  Probe   

```

我想接入的AP是MAC地址为 `74:C3:30:72:B5:7A` 的AP，由终端输出结果的 CH 列可知该AP的`channel`为13。

然后在终端输入 `airodump-ng wlan0mon --channel 13 -w saved` ,只监听该AP所在的channel，将抓包结果保存在 saved.cap 中，然后在wireshark中打开，共161KB，610个数据包。

使用 `wlam.fc.sub_type==0x0b`过滤数据包，发现我的手机向MAC地址为 `74:C3:30:72:B5:7A` 的AP 发出了auth请求，证明我的手机试图连接该AP。


![p10](https://github.com/CUCCS/2018-NS-Public-jackcily/raw/mis_chapt0x02/p10.PNG)


使用`wlan.fc.sub_type ==0x01`过滤数据包，发现该AP向我发送了Association Responce ，即我的手机成功接入了该AP。


![11](https://github.com/CUCCS/2018-NS-Public-jackcily/raw/mis_chapt0x02/p11.PNG)
      


3、SSID包含在哪些类型的802.11帧？

    由实验可知，包含SSID的数据帧如下:
        Probe Request frame(广播帧SSID 可能为空）
        Probe Response frame
        Beacon frame
        Authencition Request frame
        Authencition Responce frame

 我查阅的资料
 
 [无线接入过程](https://blog.csdn.net/hmxz2nn/article/details/79937344)
 
 [Airodump-ng](https://www.aircrack-ng.org/doku.php?id=airodump-ng)
 
 [802.11简单认证过程](https://blog.csdn.net/eydwyz/article/details/70048858)
 
