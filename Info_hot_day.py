#!/usr/bin/env python3
# coding: utf-8
from urllib import request
import urllib.request
import urllib.parse
import http.cookiejar
import json
import datetime
import sqlite3
import hashlib
import re
import time


def get_content(rank_name_group = '资讯',rank_name = '时事',date = '2016/04/11'):

    start = date
    end = date

    # url = "http://www.newrank.cn/public/info/hot.html?period=day"
    url_xhr = "http://www.newrank.cn/xdnphb/list/day/article"
    req = urllib.request.Request(url_xhr)

    # deal with headers
    ori_headers = {
        'Host': 'www.newrank.cn',
        'Connection': 'keep-alive',
        'Content-Length': '148',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Origin': 'http://www.newrank.cn',
        'X-Requested-With': 'XMLHttpRequest',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'DNT': '1',
        'Referer': 'http://www.newrank.cn/public/info/hot.html?period=day',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.6,en;q=0.4'
    }

    # set nance (0,1,2,3,4,5,6,7,8,9,a,b,c,d,e,f)9 of 16
    nonce = '012345678'

    # set xyz /*! xdnphb linux-grunt-xdnphb-copyright 2016-03-22 */
    appBase = '/xdnphb'
    urlBase = appBase+'/'
    xyz_str = urlBase + 'list/day/article?AppKey=joker&end=%s&rank_name=%s&rank_name_group=%s&start=%s' % (end, rank_name, rank_name_group, start)
    xyz = hashlib.md5((xyz_str+'&nonce='+nonce).encode()).hexdigest()

    # deal with form data
    form_data = urllib.parse.urlencode({
        'end': end,
        'rank_name': rank_name,
        'rank_name_group': rank_name_group,
        'start': start,
        'nonce': nonce,
        'xyz': xyz
    }).encode()

    # add headers to req
    for key, value in ori_headers.items():
        req.add_header(key, value)

    # deal with cookies
    cj = http.cookiejar.CookieJar()
    pro = urllib.request.HTTPCookieProcessor(cj)

    # set proxy
#    proxy_support = request.ProxyHandler({'http':'http://27.24.158.155:84'})
#    opener = urllib.request.build_opener(proxy_support, pro)
    opener = urllib.request.build_opener(pro)

    op = opener.open(req, form_data)
    data = op.read().decode("UTF-8")  # <class 'str'>

    ori_content = json.loads(data)
    inner_content = ori_content['value']
    print('正在获取 '+date.__str__()+' 的 ' + rank_name_group +' 分类下的 '+rank_name+' 数据')
    return inner_content


def get_date():
    url_xhr = "http://www.newrank.cn/xdnphb/list/getDate"
    req = urllib.request.Request(url_xhr)

    # deal with headers
    ori_headers = {
        'Host': 'www.newrank.cn',
        'Connection': 'keep-alive',
        'Content-Length': '148',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Origin': 'http://www.newrank.cn',
        'X-Requested-With': 'XMLHttpRequest',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'DNT': '1',
        'Referer': 'http://www.newrank.cn/public/info/hot.html?period=day',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.6,en;q=0.4'
    }

    # set nance (0,1,2,3,4,5,6,7,8,9,a,b,c,d,e,f)9 of 16
    nonce = '012345678'

    # set xyz /*! xdnphb linux-grunt-xdnphb-copyright 2016-03-22 */
    appBase = '/xdnphb'
    urlBase = appBase+'/'
    xyz_str = urlBase + 'list/getDate?AppKey=joker'
    xyz = hashlib.md5((xyz_str+'&nonce='+nonce).encode()).hexdigest()

    # deal with form data
    form_data = urllib.parse.urlencode({
        'nonce': nonce,
        'xyz': xyz
    }).encode()

    # add headers to req
    for key, value in ori_headers.items():
        req.add_header(key, value)

    # deal with cookies
    cj = http.cookiejar.CookieJar()
    pro = urllib.request.HTTPCookieProcessor(cj)
    opener = urllib.request.build_opener(pro)

    op = opener.open(req, form_data, timeout=2)
    data = op.read().decode("UTF-8")  # <class 'str'>

    ori_content = json.loads(data)
    inner_content = ori_content['value']['WEIXIN_CAL_DAY'][:10]
    return inner_content


def store_to_db(content,table_name):

    for x in range(len(content)):
        if content[x].get('summary',-1) == -1:
            content[x]['summary'] = None

    # sql_create, sql_insert
    sc = ''''''
    sii = ""
    i = 0
    sort_content = sorted(content[0].items(), key=lambda d: d[0])
    count = len(sort_content)
    while i < count:
        sc += '''%s TEXT,''' % sort_content[i][0]
        sii += "content[index]['%s']," % sort_content[i][0]
        i += 1

    si = sii[0:(len(sii)-1)]

    sc = sc[0:(len(sc)-1)]
    s = "?,"*count
    s = s[0:(len(s)-1)]
    sc = re.sub(",id TEXT",",id TEXT PRIMARY KEY NOT NULL",sc)
    sql_create = ''' CREATE TABLE IF NOT EXISTS ''' + table_name + ''' (''' + '''%s''' % sc + ''')'''
    sql_insert = "INSERT INTO "+table_name+" VALUES (" + s + ")"

    commit_count = 0

    conn = sqlite3.connect(table_name+".db")

    cur = conn.cursor()

    cur.execute(sql_create)

    L = []
    IDList = cur.execute("SELECT ID FROM "+table_name)
    for row in IDList:
        L.append(row[0])

    for index in range(len(content)):
        uid_exist = 1  # uid existed
        if content[index]['id'] in L:
            uid_exist = 1
            break
        else:
            uid_exist = 0
        if len(cur.fetchall()) == 0:
            uid_exist = 0
        if uid_exist == 1:
            print("exist")
        else:

            cur.execute(sql_insert,tuple(eval(si)))
            commit_count += 1
    # Save (commit) the changes
    conn.commit()
    print("新增 "+str(commit_count)+" 条数据")
    conn.close()
    return table_name


def get_rownum_from_db(table_name):
    conn = sqlite3.connect(table_name+".db")
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM "+table_name)
    total = cur.fetchone()
    conn.close()
    return total[0]


def main():
    getDate = get_date()
    getDate = datetime.datetime.strptime(getDate, "%Y-%m-%d").date()
    i = 0
    num = 7
    table_name = 'Info_hot_day'
    rank_name_group = '资讯'
    file_name = rank_name_group+'.txt'
    L = ['时事','民生','财富','科技','创业','汽车','楼市','职场','教育','学术','政务','企业']

    # 创建文件
    with open(file_name,'a+') as f:
        f.close()
    while i < num:
        date = (getDate + datetime.timedelta(days=-i))
        with open(file_name,'r+') as f:
            s = f.read()
            if str(date) in s:
                print(str(date)+'日的 '+rank_name_group+' 数据已抓取')
                f.close()
            else:
                for rank_name in L:
                    time.sleep(3)
                    content = get_content(rank_name_group,rank_name,date)
                    store_to_db(content,table_name)
                f.write(str(date)+'\n')
                f.close()
        i += 1

    rownum = get_rownum_from_db(table_name)
    print('数据库中共有 '+str(rownum)+' 条数据')


if __name__ == '__main__':
    main()

