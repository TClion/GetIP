#!/usr/bin/env
#coding=utf8

# version:2.0
# kali linux python 2.7.13
# author:TClion
# update:2017-09-05
# 在西刺网站高匿网页上寻找可用ip并筛选出响应快的ip存放在ip.txt中

import time
import json
import random
import gevent

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
        self.collection = self.db.ipall
        self.new_ip_num = 0             #新入库的ip数量
        self.fast_ip_num = 0            #筛选后的ip数量
        self.fast_ip_lst = []           #响应快ip的列表
        self.slow_num = 0               #不符合标准的ip数量

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
                if self.collection.find_one(ip_dict) == None:
                    self.collection.insert(ip_dict)
                    print i+' insert into mongodb'
                    self.new_ip_num += 1
            except:
                print 'new ip insert error'

    #筛选出响应快的ip
    def GetFastIp(self, item):
        i = item['ip']
        p = item['port']
        ip = 'http://' + i + ':' + p
        ip_dict = {
            'http': ip,
            'https': ip,
        }
        try:
            text = requests.get(self.testurl, proxies=ip_dict, timeout=3).text
            if i in text:
                print i+' insert into fast list'
                self.fast_ip_lst.append({i: p})
                self.fast_ip_num += 1
            else:
                self.slow_num += 1
        except:
            self.slow_num += 1
        print self.slow_num

    #将ip存入ip.txt中
    def SaveFastIp(self, fast_ip):
        with open('ip.txt', 'w') as f:     #将优质ip写入文件
            for ip in fast_ip:
                f.write(str(ip)+'\n')

    #从文件中读取ip列表
    def get_ip_lst(self):
        IpList = []
        with open('ip.txt', 'r') as f:
            lines = f.readlines()
        for ip in lines:
            ip_lst = ip.split('\'')
            i, p = ip_lst[1], ip_lst[3]
            ip_str = 'http://' + i + ':' + p
            ip_dict = {
                'http': ip_str,
                'https': ip_str,
            }
            IpList.append(ip_dict)
        return IpList

    #测试ip.txt中ip的响应速度
    def test(self, ip_lst):
        print 'fast list len is %d' % len(ip_lst)
        num = 0
        for ip in ip_lst:
            print ip['http']
            try:
                text = requests.get(self.testurl, proxies=ip, timeout=5).text
                num += 1
            except:
                continue
        print 'fast ip counts %d' % num


if __name__ == '__main__':
    Ip = GetIp()
    pool = Pool(processes=4)    #线程池
    for i in range(1, 9):
        pool.apply_async(Ip.GetIpDict, (i,))
    pool.close()
    pool.join()
    print 'new ip counts %d' % Ip.new_ip_num

    # thread = [gevent.spawn(Ip.GetFastIp02, i) for i in Ip.collection.find()]
    # gevent.joinall(thread)
    # T1 = time.time()
    # pool = Pool(processes=10)    #线程池
    # for i in Ip.collection.find():
    #     pool.apply_async(Ip.GetFastIp, (i,))
    # pool.close()
    # pool.join()
    # T2 = time.time()
    # print T2-T1

    # L = Ip.GetFastIp()
    #Ip.SaveFastIp(Ip.fast_ip_lst)
    # print Ip.fast_ip_num

    # ip = Ip.get_ip_lst()
    # Ip.test(ip)
