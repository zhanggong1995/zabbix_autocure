  zabbix自动治愈程序通过zabbix动作在agent端执行脚本，实现自动治愈；
  自动治愈的脚本需要另外添加，只需在AutoCure.conf内添加相应的路径即可。
  原理通过zabbix动作触发脚本，zabbix将触发器的各个信息（主机名，ip，监控项等。。）传递给治愈程序，程序通过与配置文件的对比，来抉择是否运行所对应的治愈脚本。执行完毕后，会将执行信息发送到钉钉群里。（通过钉钉机器人）

程序文件：
  auto_execute.py		主函数 
  defines.py 			函数库，包括程序运行的路径配置，一般配置好后不需要修改
  config_path="/etc/zabbix/script/autocure/AutoCure.conf"	功能配置的文件路径
  log_path = "/var/log/python/auto_execute.log"			日志路径
  webhook="..."										钉钉机器人的webhook，用于执行结果的通知
  AutoCure.conf				功能配置，需要执行自动治愈的项目配置
  [hostinfo]				固定session名，存放主机信息
  hostname = Zabbix server	主机名，对应zabbix配置中的hostname，如果有可见名称，此处为可见名称
  ip = 127.0.0.1				ip地址，对应zabbix配置中的ip地址
  [治愈动作1]				
  item_name=	监控项名			
  level=		触发器等级，支持中文或英文（英文首字母大写，此项按照zabbix内等级划分）
  question=	触发器名称
  value=<90	执行条件，第一个字符为 > 或 < ，监控项值满足此条件才会触发治愈动作
  script=/etc/zabbix/script/autocure/cure_script/idle.sh		执行脚本路径，建议写绝对路径
软件部署：
  基本模块依赖：commands,sys,time,logging,json,requests,os,环境python 2.7
  需安装：configparser
  1.安装pip：
    yum search pip
    yum -y install python2-pip.noarch
  2.安装configparser模块
    pip install configparser
  3.添加zabbix用户执行脚本的权限：
    chmod 755 * 
    vim /etc/zabbix/zabbix_agentd.conf
    EnableRemoteCommands=1
    systemctl restart zabbix-agented
  4.允许zabbix使用sudo执行脚本：
    zabbix ALL=(ALL)NOPASSWD:/etc/zabbix/script/autocure/auto_execute.py
    为安全起见检查zabbix登录权限为 /sbin/nologin
    同时注意配置文件内所写的脚本路径需要可执行权限
  5.zabbix web端设置
    配置动作，选择合适的触发条件，添加自定义脚本：
    配置-动作-操作-新的操作-操作细节：
      步骤1-1,
      步骤持续时间;60		
      操作类型：远程命令
      目标列表：当前主机
      类型：自定义脚本
      执行在：zabbix 客户端
      命令：sudo /etc/zabbix/script/autocure/auto_execute.py '{"host":"{HOST.NAME}","ip":"{HOST.IP}","severity":"		 
      {TRIGGER.SEVERITY}","trigger":"{TRIGGER.NAME}","date":"{EVENT.DATE}","time":"{EVENT.TIME}","item":"
      {ITEM.NAME}","value":"{ITEM.VALUE}"}'
      配置完成之后，满足该动作条件的触发器会触发此动作，从而调用agented端脚本，并传递参数。
  6.修改路径信息
      包括log的路径，本程序所在路径，以及钉钉的webhook
