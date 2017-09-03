#!/usr/bin/env
#coding=utf8

# author:TClion
# update:2017-09-03
# 在 西刺网站高匿网页上寻找可用ip并筛选出响应快的ip


import json
import random

import pymongo
import logging
import requests
import multiprocessing

from lxml import etree
from multiprocessing.dummy import Pool

header = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate, sdch',
    'Accept-Language': 'zh-CN,zh;q=0.8',
    'Cache-Control': 'max-age=0',
    'Connection': 'keep-alive',
    'Host': 'www.xicidaili.com',
    'If-None-Match': '',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'

}       #xici代理的header头


class GetIp():

    def __init__(self):
        self.Url = "http://www.xicidaili.com/nn/"           #xici代理页面
        self.testurl = 'http://ip.chinaz.com/getip.aspx'    #测试ip页面
        self.conn = pymongo.MongoClient('localhost', 27017)
        self.db = self.conn.ipdb
        self.account = self.db.ipall
        self.new_ip_num = 0                                         #要抓取的页面数，一个页面100个ip

    #从西刺网站上抓取ip，全部放在mongodb中
    def GetIpDict(self, pagenum):
        url = '%s%d' % (self.Url, pagenum)
        content = requests.get(url, headers=header).content
        data = etree.HTML(content)
        ip = data.xpath('//tr[@class="odd"]/td[2]/text()|//tr[@class=""]/td[2]/text()')
        port = data.xpath('//tr[@class="odd"]/td[3]/text()|//tr[@class=""]/td[3]/text()')
        ip_list = list(zip(ip, port))
        for i, p in ip_list:
            try:
                ip_dict = {
                    'ip': i,
                    'port': p
                }
                if self.account.find_one(ip_dict) == None:
                    self.account.insert(ip_dict)
                    self.new_ip_num += 1
            except:
                logging.debug('new ip insert error')


    #第二次筛选，从mongodb选出响应快的ip
    def GetFastIp(self):
        fast_ip = []
        for item in self.account.find():
            i = item['ip']
            p = item['port']
            ip_dict = {
                'http': 'http://' + i + ':' + p,
                'https': 'https://' + i + ':' + p,
            }
            try:
                text = requests.get(self.testurl, proxies=ip_dict, timeout=1).text
                if i in text:
                    fast_ip.append({i: p})
                else:
                    continue
            except:
                continue
        return fast_ip

    #将ip存入ip.txt中
    def SaveFastIp(self, fast_ip):
        with open('ip.txt', 'w') as f:     #将优质ip写入文件
            for ip in fast_ip:
                f.write(str(ip)+'\n')

    #从文件中读取ip列表
    def GetOne(self, num=None):
        IpList = []
        with open('ip.txt', 'r') as f:
            lines = f.readlines()
        for i in lines:
            #p = json.loads(i.replace('\'', '\"'))    # windows 将单引号换成双引号
            IpList.append(i)
        if num == None:
            return random.choice(IpList)
        else:
            return IpList

if __name__ == '__main__':
    Ip = GetIp()
    pool = Pool(processes=4)    #线程池
    for i in range(1, 2):
        pool.apply_async(Ip.GetIpDict, (i,))
    pool.apply_async(Ip.GetFastIp)
    pool.close()
    pool.join()
    # L = Ip.GetFastIp()
    # Ip.SaveFastIp(L)
    # ip = Ip.GetOne()
