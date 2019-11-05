#!/usr/bin/python2.7
#coding=utf-8
import commands,defines,sys

from defines import logger

if __name__ == "__main__":
    array = {}
    msg={}
    pre_par=sys.argv[1]

    logger.info("------------program start----------------")
    logger.info("截取到命令行："+pre_par)
    #解析zabbix消息
    try:
        msg[0]=defines.Message(pre_par)
    except Exception as e:
        logger.error("命令行解析出错：")
        logger.error(e)
        exit(-1)
    else:
        pass
        #msg[0].print_self()
    #解析配置文件
    try:
        for i in range(len(defines.sections)):
            if i==0:
                if defines.sections[0]!="hostinfo":
                    logger.error("配置文件没有主机信息!")
                    exit(-1)
                else:
                    array[i] = defines.SectionsHost(defines.config, i)
                    #array[i].print_self()
            else:
                array[i] = defines.Sections(defines.config, i)
                #array[i].print_self()
    except Exception as e:
        logger.error("配置文件出错：")
        logger.error(e)
        exit(-1)
    #判断主机名，ip，消息时间
    logger.debug("开始比较hostname,ip,时间,检查失败，程序退出")
    if 0!=defines.if_hostname_ip_correct(msg[0],array[0]):
        logger.error("hostname,ip,时间,检查失败，程序退出")
        exit(0)
    #判断是否满足配置文件所指定条件
    script_exe=''
    for i in range(1,len(defines.sections)):
        script_exe=defines.get_execute_script(msg[0],array[i])
        if script_exe==-1:
            continue
        else:
            break
    if script_exe==-1:
        logger.info("不满足执行条件，程序退出")
        exit(0)
    else:
        #执行配置文件中的治愈脚本
        logger.info("开始执行治愈脚本")
        (status, output) = commands.getstatusoutput(script_exe)
        if status!=0:
            logger.error("治愈脚本执行失败：返回码："+str(status)+"\r\n错误信息："+output)
            markdown_msg = '<font color=#00FFFF face="黑体" size=2>已触发自动治愈程序</font>  \n---  \n>**执行结果及路径：** 失败！:' + script_exe + '  \n>**程序输出信息：**  \n```  \n'
            markdown_msg += output + '  \n```  \n---'
            defines.send_message_to_dd(markdown_msg)
        else:
            logger.info("治愈脚本执行成功！:"+script_exe+"  \r"+output)
            markdown_msg = '<font color=#00FFFF face="黑体" size=2>已触发自动治愈程序</font>  \n---  \n>**执行结果及路径：** 成功！:' + script_exe + '  \n>**程序输出信息：**  \n```  \n'
            markdown_msg +=output+'  \n```  \n---'
            defines.send_message_to_dd(markdown_msg)