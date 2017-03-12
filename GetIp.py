"""从xici网站上获取可用的代理ip，并进行筛选,利用多线程和队列提高采集和筛选效率"""

import requests
from lxml import etree
import time
import json
from multiprocessing.dummy import Pool
import multiprocessing

header = {
    'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Encoding':'gzip, deflate, sdch',
    'Accept-Language':'zh-CN,zh;q=0.8',
    'Cache-Control':'max-age=0',
    'Connection':'keep-alive',
    'Host':'www.xicidaili.com',
    'If-None-Match':'',
    'Upgrade-Insecure-Requests':'1',
    'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'

}       #xici代理的header头


class GetIp():
    def __init__(self,num):
        self.Url = "http://www.xicidaili.com/nn/"           #xici代理页面
        self.testurl = 'http://ip.chinaz.com/getip.aspx'    #测试ip页面
        self.S = requests.session()
        manager = multiprocessing.Manager()
        self.Q = manager.Queue()                                #储存第一次筛选出来的ip
        self.L1 = []                                            #储存第二次筛选出来的ip
        self.num = num                                          #要抓取的页面数，一个页面100个ip

    #第一次筛选，选出可用ip pagenum是页面数
    def GetIpDict(self,pagenum):
        url = '%s%d' %(self.Url,pagenum)
        content = self.S.get(url,headers=header).content
        page = etree.HTML(content)
        ip = page.xpath('//tr[@class="odd"]/td[2]/text()|//tr[@class=""]/td[2]/text()')
        port = page.xpath('//tr[@class="odd"]/td[3]/text()|//tr[@class=""]/td[3]/text()')
        List = list(zip(ip,port))
        ipList = ['http://'+x+':'+y for x,y in List]
        for i in ipList:
            try:
                p = {'http':i}
                self.S.get(self.testurl,proxies=p,timeout=0.3)  #检测ip是否能用
                self.Q.put(p)
            except:
                pass
        if self.num == pagenum:
            self.Q.put('stop')              #在队列结尾设停止标志


    #第二次筛选，选出响应快的ip
    def GetFastIp(self):
        while True:
            if not self.Q.empty():
                pro = self.Q.get()
                if pro == 'stop':
                    break
                T1 = time.time()
                for i in range(10):         #测试一个ip访问10次的响应速度
                    try:
                        self.S.get(self.testurl,proxies=pro,timeout=0.3)
                        time.sleep(1)
                    except:
                        break
                T2 = time.time()
                Time = T2-T1
                if 11<Time<13:  #响应速度在11到13之间最佳
                    print(pro,Time)
                    self.L1.append(pro)


    def Save(self):
        f = open('ip.txt','w')     #将优质ip写入文件
        for i in self.L1:
            f.write(str(i)+'\n')
        f.close()

    #从文件中读取ip列表
    def Read(self):
        f = open('ip.txt','r')
        lines = f.readlines()
        IpList = []
        for i in lines:
            p = json.loads(i.replace('\'','\"'))    #将单引号换成双引号
            IpList.append(p)
        f.close()
        return IpList


if __name__ ==  '__main__':
    page = 10                   #抓10页，共1000个ip
    Ip = GetIp(page)
    pool = Pool(processes=4)    #线程池
    for i in range(1,page+1):
        pool.apply_async(Ip.GetIpDict,(i,))
    pool.apply_async(Ip.GetFastIp)
    pool.close()
    pool.join()
    Ip.Save()
