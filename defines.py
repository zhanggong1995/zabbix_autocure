#!/usr/bin/python2.7
# coding=utf-8

import time,logging,configparser,json
import requests,os
config_path="/usr/lib/zabbix/alertscripts/AutoCure.conf"
log_path = "/var/log/python/auto_execute.log"
logger = logging.getLogger()
logger.setLevel(level=logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# 写入日志
handler_file = logging.FileHandler(log_path)
handler_file.setLevel(logging.DEBUG)
handler_file.setFormatter(formatter)
# 标准输出
handler_stdout = logging.StreamHandler()
handler_stdout.setLevel(logging.DEBUG)
handler_stdout.setFormatter(formatter)

logger.addHandler(handler_file)
logger.addHandler(handler_stdout)
config = configparser.ConfigParser()
#config.read("/usr/lib/zabbix/alertscripts/AutoCure.conf", encoding="utf-8")
if not os.path.exists(config_path):
    logger.error("配置文件不存在！")
    exit(-1)
config.read(config_path,encoding="utf-8")
sections=config.sections()

trigger_level={
    "Not classified":1,
    "Information":2,
    "Warning":3,
    "Average":4,
    "High":5,
    "Disaster":6,
    "未分类":1,
    "信息":2,
    "警告":3,
    "一般严重":4,
    "严重":5,
    "灾难":6
}
class Message(object):
    def __init__(self,argv):
        self.all_parameter=json.loads(argv)
        self.hostname       =self.all_parameter["host"].encode("utf-8")
        print self.hostname
        self.ip             =self.all_parameter["ip"].encode("utf-8")
        print self.ip
        self.trigger_name   =self.all_parameter["trigger"].encode("utf-8")
        print self.trigger_name
        self.trigger_severity=trigger_level[self.all_parameter["severity"].encode("utf-8")]
        print self.trigger_severity
        self.date           =self.all_parameter["date"].encode("utf-8")
        print self.date
        self.time           =self.all_parameter["time"].encode("utf-8")
        print self.time
        self.item_name      =self.all_parameter["item"].encode("utf-8")
        print self.item_name
        self.item_value     =self.all_parameter["value"].encode("utf-8")
        print self.item_value

class SectionsHost(object):
    def __init__(self,configure,num):
        section = (configure.sections())
        self.item_name  =section[num].encode("utf-8")
        print("["+self.item_name+"]")
        self.hostname   =configure.get(section[num], "hostname").encode("utf-8")
        print self.hostname
        self.ip         =str(configure.get(section[num], "ip")).encode("utf-8")
        print self.ip

class Sections(object):
    def __init__(self,configure,num):
        section = (configure.sections())
        self.name  =section[num].encode("utf-8")
        print self.name
        self.item_name  =configure.get(section[num], "item_name").encode("utf-8")
        print self.item_name
        self.level      =trigger_level[configure.get(section[num], "level").encode("utf-8")]
        print self.level
        self.question   =configure.get(section[num], "question").encode("utf-8")
        print self.question
        #self.value=str(value[0])
        self.value      =configure.get(section[num], "value").encode("utf-8")
        print self.value
        self.script=configure.get(section[num], "script").encode("utf-8")
        print self.script
def compare_date_time(msg_date,msg_time):
    msg_data_time = msg_date + " " + msg_time
    try:
        timeArray = time.strptime(msg_data_time, "%Y.%m.%d %H:%M:%S")
    except Exception as e:
        logger.error(str(e)+"时间格式不正确，期待格式 %Y.%m.%d %H:%M:%S " )
        return 2
    else:
        timeStamp = int(time.mktime(timeArray))
        now = int(time.time())
        if abs(now-timeStamp) > 60*10:
            logger.info("时间验证失败，接收消息时间已超过10分钟")
            return 1
        else:
            return 0
def compare_value(msg_value,value):
    compare_cmd = value[0]
    abs_msg_value = filter(str.isdigit, str(msg_value))
    abs_value = filter(str.isdigit, str(value))

    if compare_cmd == "<":
        if abs_msg_value < abs_value:
            return 0
        else:
            return -1
    elif value[0] == ">":
        if abs_msg_value > abs_value:
            return 0
        else:
            return -1
    else:
        logger.error("判断符："+compare_cmd+" 配置文件格式错误，value开始的格式应为 > <")
def if_hostname_ip_correct(message,session_host):
    if message.hostname!=session_host.hostname or message.ip!=session_host.ip:
        logger.info("主机名或ip不匹配")
        logger.info("msg.hostname="+message.hostname+"conf.hostname="+session_host.hostname)
        logger.info("msg.ip=" + message.ip + "conf.ip=" + session_host.ip)
        return -1
    if compare_date_time(message.date,message.time)!=0:
        logger.info("消息时间过旧")
        return -1
    else:
        return 0
def get_execute_script(message,sessions):
    if message.item_name!=sessions.item_name:
        logger.info("监控项名不匹配:msg:"+message.item_name+" conf:"+sessions.item_name)
        return -1
    if message.trigger_name!=sessions.question:
        logger.info("触发器名不匹配:msg:"+message.trigger_name+" conf:"+sessions.question)
        return -1
    if message.trigger_severity < sessions.level:
        logger.info("触发器等级低于配置文件："+str(message.trigger_severity)+"<"+str(sessions.level))
        return -1
    if compare_value(message.item_value,sessions.value)!=0:
        logger.info("触发值未到配置文件设定值:msg:"+message.item_value+" conf:"+sessions.value)
        return -1
    logger.info("满足所有条件，提取脚本路径："+sessions.script)
    return str(sessions.script)
def send_message_to_dd(text):
    webhook = "https://oapi.dingtalk.com/robot/send?access_token=fa5e88a289b4ebaae9d28bac5b1a2f78be685023493322ec77bcbe7571739da1"
    user = "Autocure-program"
    json_text = {
        "msgtype": "markdown",
        "markdown": {
            "title": "自动治愈信息",
            "text": text
        },
        "at": {
            "atMobiles": [
                user
            ],
            "isAtAll": False
        }
    }
    headers = {'Content-Type': 'application/json'}
    try:
        x = requests.post(webhook, json.dumps(json_text), headers=headers).json()

        if x["errcode"] == 0:
           logger.info("钉钉消息发送成功："+str(text))
        else:
            logger.info("钉钉消息发送失败：code："+str(x["errcode"]))
    except Exception as e:
        logger.error("钉钉消息request过程出错:"+str(e))