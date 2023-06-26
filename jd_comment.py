# -*- coding: utf-8 -*-
# 自动带图评价、追评、服务评价，需电脑端CK
# @Time : 2022/11/4
# @Author : @qiu-lzsnmb and @Dimlitter @Dylan
# @File : auto_comment.py
# 多账号评价，异常处理
# 2023/3/28 修复乱码
# 2023/4/19 当存在OPENAI_API_KEY环境变量时，启用AI评价；网络支持：1.环境变量OPENAI_API_BASE_URL反向代理、2.ProxyUrl代理、3.环境支持直连；
'''
new Env('自动评价');
8 8 2 1 * https://raw.githubusercontent.com/6dylan6/auto_comment/main/jd_comment.py
'''
import argparse
import copy
import logging
import os
import random
import sys
import time,re
import urllib.parse

try:
    import jieba  # just for linting
    import jieba.analyse
    import requests
    #import yaml
    from lxml import etree
    import zhon.hanzi
    
except:
    print('解决依赖问题...稍等')
    os.system('pip3 install lxml &> /dev/null')
    os.system('pip3 install jieba &> /dev/null')
    os.system('pip3 install zhon &> /dev/null')
    os.system('pip3 install requests &> /dev/null')
    os.system('pip3 install urllib3==1.25.11 &> /dev/null')
    import jieba 
    import jieba.analyse
    #import yaml
    from lxml import etree
    import requests
    import urllib.parse
import jdspider
# constants
CONFIG_PATH = './config.yml'
USER_CONFIG_PATH = './config.user.yml'
ORDINARY_SLEEP_SEC = 10
SUNBW_SLEEP_SEC = 5
REVIEW_SLEEP_SEC = 10
SERVICE_RATING_SLEEP_SEC = 15

## logging with styles
## Reference: https://stackoverflow.com/a/384125/12002560
_COLORS = {
    'black': 0,
    'red': 1,
    'green': 2,
    'yellow': 3,
    'blue': 4,
    'magenta': 5,
    'cyan': 6,
    'white': 7
}

_RESET_SEQ = '\033[0m'
_COLOR_SEQ = '\033[1;%dm'
_BOLD_SEQ = '\033[1m'
_ITALIC_SEQ = '\033[3m'
_UNDERLINED_SEQ = '\033[4m'

_FORMATTER_COLORS = {
    'DEBUG': _COLORS['blue'],
    'INFO': _COLORS['green'],
    'WARNING': _COLORS['yellow'],
    'ERROR': _COLORS['red'],
    'CRITICAL': _COLORS['red']
}

def format_style_seqs(msg, use_style=True):
    if use_style:
        msg = msg.replace('$RESET', _RESET_SEQ)
        msg = msg.replace('$BOLD', _BOLD_SEQ)
        msg = msg.replace('$ITALIC', _ITALIC_SEQ)
        msg = msg.replace('$UNDERLINED', _UNDERLINED_SEQ)
    else:
        msg = msg.replace('$RESET', '')
        msg = msg.replace('$BOLD', '')
        msg = msg.replace('$ITALIC', '')
        msg = msg.replace('$UNDERLINED', '')

class StyleFormatter(logging.Formatter):
    def __init__(self, fmt=None, datefmt=None, use_style=True):
        logging.Formatter.__init__(self, fmt, datefmt)
        self.use_style = use_style

    def format(self, record):
        rcd = copy.copy(record)
        levelname = rcd.levelname
        if self.use_style and levelname in _FORMATTER_COLORS:
            levelname_with_color = '%s%s%s' % (
                _COLOR_SEQ % (30 + _FORMATTER_COLORS[levelname]),
                levelname, _RESET_SEQ)
            rcd.levelname = levelname_with_color
        return logging.Formatter.format(self, rcd)


# 评价生成
def generation(pname, _class=0, _type=1, opts=None):
    if "OPENAI_API_KEY" in os.environ:
        return generation_ai(pname, opts)
    opts = opts or {}
    items = ['商品名']
    items.clear()
    items.append(pname)
    opts['logger'].debug('Items: %s', items)
    loop_times = len(items)
    opts['logger'].debug('Total loop times: %d', loop_times)
    for i, item in enumerate(items):
        opts['logger'].debug('Loop: %d / %d', i + 1, loop_times)
        opts['logger'].debug('Current item: %s', item)
        spider = jdspider.JDSpider(item,ck)
        opts['logger'].debug('Successfully created a JDSpider instance')
        # 增加对增值服务的评价鉴别
        if "赠品" in pname or "非实物" in pname or "京服无忧" in pname or "权益" in pname or "非卖品" in pname or "增值服务" in pname:
            result = [
                "赠品挺好的。",
                "很贴心，能有这样免费赠送的赠品!",
                "正好想着要不要多买一份增值服务，没想到还有这样的赠品。",
                "赠品正合我意。",
                "赠品很好，挺不错的。",
                "本来买了产品以后还有些担心。但是看到赠品以后就放心了。",
                "不论品质如何，至少说明店家对客的态度很好！",
                "我很喜欢这些商品！",
                "我对于商品的附加值很在乎，恰好这些赠品为这件商品提供了这样的的附加值，这令我很满意。"
                "感觉现在的网购环境环境越来越好了，以前网购的时候还没有过么多贴心的赠品和增值服务",
                "第一次用京东，被这种赠品和增值服物的良好态度感动到了。",
                "赠品还行。"
            ]
        else:
            result = spider.getData(4, 3)  # 这里可以自己改
        opts['logger'].debug('Result: %s', result)

    # class 0是评价 1是提取id
    try:
        name = jieba.analyse.textrank(pname, topK=5, allowPOS='n')[0]
        opts['logger'].debug('Name: %s', name)
    except Exception as e:
    #    opts['logger'].warning(
    #        'jieba textrank analysis error: %s, name fallback to "宝贝"', e)
        name = "宝贝"
    if _class == 1:
        opts['logger'].debug('_class is 1. Directly return name')
        return name
    else:
        if _type == 1:
            num = 6
        elif _type == 0:
            num = 4
        num = min(num, len(result))
        # use `.join()` to improve efficiency
        comments = ''.join(random.sample(result, num))
        opts['logger'].debug('_type: %d', _type)
        opts['logger'].debug('num: %d', num)
        opts['logger'].debug('Raw comments: %s', comments)

        return 5, comments.replace("$", name)

# ChatGPT评价生成
def generation_ai(pname, _class=0, _type=1, opts=None):
    # 当存在 OPENAI_API_BASE_URL 时，使用反向代理
    api_base_url = os.environ.get("OPENAI_API_BASE_URL", "https://api.openai.com")
    api_key = os.environ["OPENAI_API_KEY"]
    prompt = f"{pname} 写一段此商品的评价，简短、口语化"
    response = requests.post(
        f"{api_base_url}/v1/chat/completions",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        json={
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1024,
        }
    )
    response_text = response.json()
    if "error" in response_text:
        print("\nOpenAI API 调用错误：\n", response_text["error"]["message"])
        exit()
    else:
        return 5, response_text["choices"][0]["message"]["content"].strip()


# 查询全部评价
def all_evaluate(opts=None):
    try:
        opts = opts or {}
        N = {}
        url = 'https://club.jd.com/myJdcomments/myJdcomment.action?'
        opts['logger'].debug('URL: %s', url)
        opts['logger'].debug('Fetching website data')
        req = requests.get(url, headers=headers)
        opts['logger'].debug(
            'Successfully accepted the response with status code %d',
            req.status_code)
        if not req.ok:
            opts['logger'].warning(
                'Status code of the response is %d, not 200', req.status_code)
        req_et = etree.HTML(req.text)
        opts['logger'].debug('Successfully parsed an XML tree')
        evaluate_data = req_et.xpath('//*[@id="main"]/div[2]/div[1]/div/ul/li')
        loop_times = len(evaluate_data)
        opts['logger'].debug('Total loop times: %d', loop_times)
        for i, ev in enumerate(evaluate_data):
            opts['logger'].debug('Loop: %d / %d', i + 1, loop_times)
            na = ev.xpath('a/text()')[0]
            opts['logger'].debug('na: %s', na)
            #print(ev.xpath('b/text()')[0])
            try:
                num = ev.xpath('b/text()')[0]
                opts['logger'].debug('num: %s', num)
            except IndexError:
                #opts['logger'].warning('Can\'t find num content in XPath, fallback to 0')
                num = 0
            N[na] = int(num)
        return N
    except Exception as e:
        print (e)

# 评价晒单
def sunbw(N, opts=None):
    try:
        opts = opts or {}
        Order_data = []
        req_et = []
        loop_times = 2
        opts['logger'].debug('Fetching website data')
        opts['logger'].debug('Total loop times: %d', loop_times)
        for i in range(loop_times):
            url = (f'https://club.jd.com/myJdcomments/myJdcomment.action?sort=0&'
                   f'page={i + 1}')
            opts['logger'].debug('URL: %s', url)
            req = requests.get(url, headers=headers)
            opts['logger'].debug(
                'Successfully accepted the response with status code %d',
                req.status_code)
            if not req.ok:
                opts['logger'].warning(
                    'Status code of the response is %d, not 200', req.status_code)
            req_et.append(etree.HTML(req.text))
            opts['logger'].debug('Successfully parsed an XML tree')
        opts['logger'].debug('Fetching data from XML trees')
        opts['logger'].debug('Total loop times: %d', loop_times)
        for idx, i in enumerate(req_et):
            opts['logger'].debug('Loop: %d / %d', idx + 1, loop_times)
            opts['logger'].debug('Fetching order data in the default XPath')
            elems = i.xpath(
                '//*[@id="main"]/div[2]/div[2]/table/tbody')
            opts['logger'].debug('Count of fetched order data: %d', len(elems))
            Order_data.extend(elems)
        #if len(Order_data) != N['待评价订单']:
        #    opts['logger'].debug(
        #        'Count of fetched order data doesn\'t equal N["待评价订单"]')
        #    opts['logger'].debug('Clear the list Order_data')
        #    Order_data = []
        #    opts['logger'].debug('Total loop times: %d', loop_times)
        #    for idx, i in enumerate(req_et):
        #        opts['logger'].debug('Loop: %d / %d', idx + 1, loop_times)
        #        opts['logger'].debug('Fetching order data in another XPath')
        #        elems = i.xpath(
        #            '//*[@id="main"]/div[2]/div[2]/table')
        #        opts['logger'].debug('Count of fetched order data: %d', len(elems))
        #        Order_data.extend(elems)
    
        opts['logger'].info(f"当前共有{N['待评价订单']}个评价。")
        opts['logger'].debug('Commenting on items')
        for i, Order in enumerate(reversed(Order_data)):
            if i + 1 > 10:
                opts['logger'].info(f'\n已评价10个订单，跳出')
                break
            try:
                oid = Order.xpath('tr[@class="tr-th"]/td/span[3]/a/text()')[0]
                opts['logger'].debug('oid: %s', oid)
                oname_data = Order.xpath(
                    'tr[@class="tr-bd"]/td[1]/div[1]/div[2]/div/a/text()')
                opts['logger'].debug('oname_data: %s', oname_data)
                pid_data = Order.xpath(
                    'tr[@class="tr-bd"]/td[1]/div[1]/div[2]/div/a/@href')
                opts['logger'].debug('pid_data: %s', pid_data)
            except IndexError:
                opts['logger'].warning(f"第{i + 1}个订单未查找到商品，跳过。")
                continue
            loop_times1 = min(len(oname_data), len(pid_data))
            opts['logger'].debug('Commenting on orders')
            opts['logger'].debug('Total loop times: %d', loop_times1)
            idx = 0
            for oname, pid in zip(oname_data, pid_data):
                pid = re.findall('(?<=jd.com/)[(0-9)*?]+',pid)[0]
                opts['logger'].info(f'\n开始第{i+1}个订单: {oid}')
                opts['logger'].debug('pid: %s', pid)
                opts['logger'].debug('oid: %s', oid)
                xing, Str = generation(oname, opts=opts)
                opts['logger'].info(f'评价信息：{xing}星  ' + Str)
                # 获取图片
                url1 = (f'https://club.jd.com/discussion/getProductPageImageCommentList'
                        f'.action?productId={pid}')
                opts['logger'].debug('Fetching images using the default URL')
                opts['logger'].debug('URL: %s', url1)
                req1 = requests.get(url1, headers=headers)
                opts['logger'].debug(
                    'Successfully accepted the response with status code %d',
                    req1.status_code)
                if not req1.ok:
                    opts['logger'].warning(
                        'Status code of the response is %d, not 200', req1.status_code)
                imgdata = req1.json()
                opts['logger'].debug('Image data: %s', imgdata)
                if imgdata["imgComments"]["imgCommentCount"] > 10:
                    pnum = random.randint(2,int(imgdata["imgComments"]["imgCommentCount"]/10)+1)
                    opts['logger'].debug('Count of fetched image comments is 0')
                    opts['logger'].debug('Fetching images using another URL')
                    url1 = (f'https://club.jd.com/discussion/getProductPageImage'
                            f'CommentList.action?productId={pid}&page={pnum}')
                    opts['logger'].debug('URL: %s', url1)
                    time.sleep(1)
                    req1 = requests.get(url1, headers=headers)
                    opts['logger'].debug(
                        'Successfully accepted the response with status code %d',
                        req1.status_code)
                    if not req1.ok:
                        opts['logger'].warning(
                            'Status code of the response is %d, not 200',
                            req1.status_code)
                    imgdata2 = req1.json()
                    opts['logger'].debug('Image data: %s', imgdata2)
                try:
                    imgurl = random.choice(imgdata["imgComments"]["imgList"])["imageUrl"]
                    if ('imgdata2' in dir()):
                        imgurl2 = random.choice(imgdata2["imgComments"]["imgList"])["imageUrl"]
                    else:
                        imgurl2 = ''
                except Exception:
                    imgurl = ''
                    imgurl2 = ''
                opts['logger'].debug('Image URL: %s', imgurl)
                
                opts['logger'].info(f'图片：{imgurl + "," + imgurl2}')
                # 提交晒单
                opts['logger'].debug('Preparing for commenting')
                url2 = "https://club.jd.com/myJdcomments/saveProductComment.action"
                opts['logger'].debug('URL: %s', url2)
                headers['Referer'] = ('https://club.jd.com/myJdcomments/orderVoucher.action')
                headers['Origin'] = 'https://club.jd.com'
                headers['Content-Type'] = 'application/x-www-form-urlencoded'
                opts['logger'].debug('New header for this request: %s', headers)
                data = {
                 'orderId': oid,
                 'productId': pid,
                 'score': str(xing),  # 商品几星
                 'content': urllib.parse.quote(Str),  # 评价内容
                 'imgs': imgurl + ',' + imgurl2,
                 'saveStatus': 2,
                 'anonymousFlag': 1
                 }
                opts['logger'].debug('Data: %s', data)
                if not opts.get('dry_run'):
                    opts['logger'].debug('Sending comment request')
                    pj2 = requests.post(url2, headers=headers, data=data)
                    if pj2.ok:
                        opts['logger'].info(f'提交成功！')
                else:
                    opts['logger'].debug(
                        'Skipped sending comment request in dry run')
                opts['logger'].debug('Sleep time (s): %.1f', ORDINARY_SLEEP_SEC)
                time.sleep(ORDINARY_SLEEP_SEC)
                idx += 1
        N['待评价订单'] -= 1
        return N
    except Exception as e:
        print (e)

# 追评
def review(N, opts=None):
    try:
        opts = opts or {}
        req_et = []
        Order_data = []
        loop_times = 2
        opts['logger'].debug('Fetching website data')
        opts['logger'].debug('Total loop times: %d', loop_times)
        for i in range(loop_times):
            opts['logger'].debug('Loop: %d / %d', i + 1, loop_times)
            url = (f"https://club.jd.com/myJdcomments/myJdcomment.action?sort=3"
                   f"&page={i + 1}")
            opts['logger'].debug('URL: %s', url)
            req = requests.get(url, headers=headers)
            opts['logger'].debug(
                'Successfully accepted the response with status code %d',
                req.status_code)
            if not req.ok:
                opts['logger'].warning(
                    'Status code of the response is %d, not 200', req.status_code)
            req_et.append(etree.HTML(req.text))
            opts['logger'].debug('Successfully parsed an XML tree')
        opts['logger'].debug('Fetching data from XML trees')
        opts['logger'].debug('Total loop times: %d', loop_times)
        for idx, i in enumerate(req_et):
            opts['logger'].debug('Loop: %d / %d', idx + 1, loop_times)
            opts['logger'].debug('Fetching order data in the default XPath')
            elems = i.xpath(
                '//*[@id="main"]/div[2]/div[2]/table/tr[@class="tr-bd"]')
            opts['logger'].debug('Count of fetched order data: %d', len(elems))
            Order_data.extend(elems)
        #if len(Order_data) != N['待追评']:
        #    opts['logger'].debug(
        #        'Count of fetched order data doesn\'t equal N["待追评"]')
        #    # NOTE: Need them?
        #    # opts['logger'].debug('Clear the list Order_data')
        #    # Order_data = []
        #    opts['logger'].debug('Total loop times: %d', loop_times)
        #    for idx, i in enumerate(req_et):
        #        opts['logger'].debug('Loop: %d / %d', idx + 1, loop_times)
        #        opts['logger'].debug('Fetching order data in another XPath')
        #        elems = i.xpath(
        #            '//*[@id="main"]/div[2]/div[2]/table/tbody/tr[@class="tr-bd"]')
        #        opts['logger'].debug('Count of fetched order data: %d', len(elems))
        #        Order_data.extend(elems)
        opts['logger'].info(f"当前共有{N['待追评']}个需要追评。")
        opts['logger'].debug('Commenting on items')
        for i, Order in enumerate(reversed(Order_data)):
            if i + 1 > 10:
                opts['logger'].info(f'\n已评价10个订单，跳出')
                break
            oname = Order.xpath('td[1]/div/div[2]/div/a/text()')[0]
            _id = Order.xpath('td[3]/div/a/@href')[0]
            opts['logger'].debug('_id: %s', _id)
            url1 = ("https://club.jd.com/afterComments/"
                    "saveAfterCommentAndShowOrder.action")
            opts['logger'].debug('URL: %s', url1)
            pid, oid = _id.replace(
                'http://club.jd.com/afterComments/productPublish.action?sku=',
                "").split('&orderId=')
            opts['logger'].debug('pid: %s', pid)
            opts['logger'].debug('oid: %s', oid)
            opts['logger'].info(f'\n开始第{i+1}个订单: {oid}')
            _, context = generation(oname, _type=0, opts=opts)
            opts['logger'].info(f'追评内容：{context}')
            data1 = {
                'orderId': oid,
                'productId': pid,
                'content': urllib.parse.quote(context),
                'anonymousFlag': 1,
                'score': 5
            }
            opts['logger'].debug('Data: %s', data1)
            if not opts.get('dry_run'):
                opts['logger'].debug('Sending comment request')
                req_url1 = requests.post(url1, headers=headers, data=data1)
                if req_url1.ok:
                    opts['logger'].info(f'提交成功！')
            else:
                opts['logger'].debug('Skipped sending comment request in dry run')
            opts['logger'].debug('Sleep time (s): %.1f', REVIEW_SLEEP_SEC)
            time.sleep(REVIEW_SLEEP_SEC)
            N['待追评'] -= 1
        return N
    except Exception as e:
        print (e)

# 服务评价
def Service_rating(N, opts=None):
    try:
        opts = opts or {}
        Order_data = []
        req_et = []
        loop_times = 2
        opts['logger'].debug('Fetching website data')
        opts['logger'].debug('Total loop times: %d', loop_times)
        for i in range(loop_times):
            opts['logger'].debug('Loop: %d / %d', i + 1, loop_times)
            url = (f"https://club.jd.com/myJdcomments/myJdcomment.action?sort=4"
                   f"&page={i + 1}")
            opts['logger'].debug('URL: %s', url)
            req = requests.get(url, headers=headers)
            opts['logger'].debug(
                'Successfully accepted the response with status code %d',
                req.status_code)
            if not req.ok:
                opts['logger'].warning(
                    'Status code of the response is %d, not 200', req.status_code)
            req_et.append(etree.HTML(req.text))
            opts['logger'].debug('Successfully parsed an XML tree')
        opts['logger'].debug('Fetching data from XML trees')
        opts['logger'].debug('Total loop times: %d', loop_times)
        for idx, i in enumerate(req_et):
            opts['logger'].debug('Loop: %d / %d', idx + 1, loop_times)
            opts['logger'].debug('Fetching order data in the default XPath')
            elems = i.xpath(
                '//*[@id="main"]/div[2]/div[2]/table/tbody/tr[@class="tr-th"]')
            opts['logger'].debug('Count of fetched order data: %d', len(elems))
            Order_data.extend(elems)
   #    if len(Order_data) != N['服务评价']:
   #        opts['logger'].debug(
   #            'Count of fetched order data doesn\'t equal N["服务评价"]')
   #        opts['logger'].debug('Clear the list Order_data')
   #        Order_data = []
   #        opts['logger'].debug('Total loop times: %d', loop_times)
   #        for idx, i in enumerate(req_et):
   #            opts['logger'].debug('Loop: %d / %d', idx + 1, loop_times)
   #            opts['logger'].debug('Fetching order data in another XPath')
   #            elems = i.xpath(
   #                '//*[@id="main"]/div[2]/div[2]/table/tr[@class="tr-bd"]')
   #            opts['logger'].debug('Count of fetched order data: %d', len(elems))
   #            Order_data.extend(elems)
        opts['logger'].info(f"当前共有{N['服务评价']}个需要服务评价。")
        opts['logger'].debug('Commenting on items')
        for i, Order in enumerate(reversed(Order_data)):
            if i + 1 > 10:
                opts['logger'].info(f'\n已评价10个订单，跳出')
                break
            #oname = Order.xpath('td[1]/div[1]/div[2]/div/a/text()')[0]
            oid = Order.xpath('td[1]/span[3]/a/text()')[0]
            opts['logger'].info(f'\n开始第{i+1}个订单: {oid}')
            opts['logger'].debug('oid: %s', oid)
            url1 = (f'https://club.jd.com/myJdcomments/insertRestSurvey.action'
                    f'?voteid=145&ruleid={oid}')
            opts['logger'].debug('URL: %s', url1)
            data1 = {
                'oid': oid,
                'gid': '32',
                'sid': '186194',
                'stid': '0',
                'tags': '',
                'ro591': f'591A{random.randint(4, 5)}',  # 商品符合度
                'ro592': f'592A{random.randint(4, 5)}',  # 店家服务态度
                'ro593': f'593A{random.randint(4, 5)}',  # 快递配送速度
                'ro899': f'899A{random.randint(4, 5)}',  # 快递员服务
                'ro900': f'900A{random.randint(4, 5)}'  # 快递员服务
            }
            opts['logger'].debug('Data: %s', data1)
            if not opts.get('dry_run'):
                opts['logger'].debug('Sending comment request')
                pj1 = requests.post(url1, headers=headers, data=data1)
                if pj1.ok:
                    opts['logger'].info(f'提交成功！')
            else:
                opts['logger'].debug('Skipped sending comment request in dry run')
            #opts['logger'].info("\n " + pj1.text)
            opts['logger'].debug('Sleep time (s): %.1f', SERVICE_RATING_SLEEP_SEC)
            time.sleep(SERVICE_RATING_SLEEP_SEC)
            N['服务评价'] -= 1
        return N
    except Exception as e:
        print (e)

def No(opts=None):
    opts = opts or {}
    opts['logger'].info('')
    N = all_evaluate(opts)
    s = '----'.join(['{} {}'.format(i, N[i]) for i in N])
    opts['logger'].info(s)
    opts['logger'].info('')
    return N


def main(opts=None):
    opts = opts or {}
    #opts['logger'].info("开始京东自动评价！")
    N = No(opts)
    opts['logger'].debug('N value after executing No(): %s', N)
    if not N:
        opts['logger'].error('CK错误，请确认是否电脑版CK！')
        return
    if N['待评价订单'] != 0:
        opts['logger'].info("1.开始评价晒单")
        N = sunbw(N, opts)
        opts['logger'].debug('N value after executing sunbw(): %s', N)
        N = No(opts)
        opts['logger'].debug('N value after executing No(): %s', N)
    if N['待追评'] != 0:
       opts['logger'].info("2.开始追评！")
       N = review(N, opts)
       opts['logger'].debug('N value after executing review(): %s', N)
       N = No(opts)
       opts['logger'].debug('N value after executing No(): %s', N)
    if N['服务评价'] != 0:
        opts['logger'].info('3.开始服务评价')
        N = Service_rating(N, opts)
        opts['logger'].debug('N value after executing Service_rating(): %s', N)
        N = No(opts)
        opts['logger'].debug('N value after executing No(): %s', N)
    opts['logger'].info("该账号运行完成！")


if __name__ == '__main__':
    # parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run',
                        help='have a full run without comment submission',
                        action='store_true')
    parser.add_argument('--log-level',
                        help='specify logging level (default: info)',
                        default='INFO')
    parser.add_argument('-o', '--log-file', help='specify logging file')
    args = parser.parse_args()
    if args.log_level.upper() not in [
        'DEBUG', 'WARN', 'INFO', 'ERROR', 'FATAL'
        # NOTE: `WARN` is an alias of `WARNING`. `FATAL` is an alias of
        # `CRITICAL`. Using these aliases is for developers' and users'
        # convenience.
        # NOTE: Now there is no logging on `CRITICAL` level.
    ]:
        args.log_level = 'INFO'
    else:
        args.log_level = args.log_level.upper()
    opts = {
        'dry_run': args.dry_run,
        'log_level': args.log_level
    }
    if "DEBUG" in os.environ and os.environ["DEBUG"] == 'true':
        opts = {
            'dry_run': args.dry_run,
            'log_level': 'DEBUG'
    }      
    if hasattr(args, 'log_file'):
        opts['log_file'] = args.log_file
    else:
        opts['log_file'] = None

    # logging on console
    _logging_level = getattr(logging, opts['log_level'])
    logger = logging.getLogger('comment')
    logger.setLevel(level=_logging_level)
    # NOTE: `%(levelname)s` will be parsed as the original name (`FATAL` ->
    # `CRITICAL`, `WARN` -> `WARNING`).
    # NOTE: The alignment number should set to 19 considering the style
    # controling characters. When it comes to file logger, the number should
    # set to 8.
    formatter = StyleFormatter('%(asctime)s %(levelname)-19s %(message)s',"%F %T")
    rawformatter = StyleFormatter('%(asctime)s %(levelname)-8s %(message)s', use_style=False)
    console = logging.StreamHandler()
    console.setLevel(_logging_level)
    console.setFormatter(logging.Formatter('%(message)s'))
    logger.addHandler(console)
    opts['logger'] = logger
    # It's a hack!!!
    jieba.default_logger = logging.getLogger('jieba')
    jieba.default_logger.setLevel(level=_logging_level)
    jieba.default_logger.addHandler(console)
    # It's another hack!!!
    jdspider.default_logger = logging.getLogger('spider')
    jdspider.default_logger.setLevel(level=_logging_level)
    jdspider.default_logger.addHandler(console)

    logger.debug('Successfully set up console logger')
    logger.debug('CLI arguments: %s', args)
    logger.debug('Opening the log file')
    if opts['log_file']:
        try:
            handler = logging.FileHandler(opts['log_file'])
        except Exception as e:
            logger.error('Failed to open the file handler')
            logger.error('Error message: %s', e)
            sys.exit(1)
        handler.setLevel(_logging_level)
        handler.setFormatter(rawformatter)
        logger.addHandler(handler)
        jieba.default_logger.addHandler(handler)
        jdspider.default_logger.addHandler(handler)
        logger.debug('Successfully set up file logger')
    logger.debug('Options passed to functions: %s', opts)
    logger.debug('Builtin constants:')
    logger.debug('  CONFIG_PATH: %s', CONFIG_PATH)
    logger.debug('  USER_CONFIG_PATH: %s', USER_CONFIG_PATH)
    logger.debug('  ORDINARY_SLEEP_SEC: %s', ORDINARY_SLEEP_SEC)
    logger.debug('  SUNBW_SLEEP_SEC: %s', SUNBW_SLEEP_SEC)
    logger.debug('  REVIEW_SLEEP_SEC: %s', REVIEW_SLEEP_SEC)
    logger.debug('  SERVICE_RATING_SLEEP_SEC: %s', SERVICE_RATING_SLEEP_SEC)

    # parse configurations
    #logger.debug('Reading the configuration file')
    #if os.path.exists(USER_CONFIG_PATH):
        #logger.debug('User configuration file exists')
        #_cfg_path = USER_CONFIG_PATH
    #else:
        #logger.debug('User configuration file doesn\'t exist, fallback to the default one')
        #_cfg_path = CONFIG_PATH
   # with open(_cfg_path, 'r', encoding='utf-8') as f:
        #cfg = yaml.safe_load(f)
        #print()
    #logger.debug('Closed the configuration file')
    #logger.debug('Configurations in Python-dict format: %s', cfg)
    cks = []
    if "PC_COOKIE" in os.environ:
        if len(os.environ["PC_COOKIE"]) > 200:
            if '&' in os.environ["PC_COOKIE"]:
                cks = os.environ["PC_COOKIE"].split('&')
            else:
                cks.append(os.environ["PC_COOKIE"])
        else:
            logger.info ("CK错误，请确认是否电脑版CK！")
            sys.exit(1)
        logger.info ("已获取环境变量 CK")       
    else:
        logger.info("没有设置变量PC_COOKIE，请添加电脑端CK到环境变量")
        sys.exit(1)
    if "OPENAI_API_KEY" in os.environ:
        logger.info('已启用AI评价')
        if "OPENAI_API_BASE_URL" in os.environ:
            logger.info('  - 使用 OpenAI API 代理：' + os.environ["OPENAI_API_BASE_URL"])
        elif os.environ.get("ProxyUrl").startswith("http"):
            os.environ['http_proxy'] = os.getenv("ProxyUrl")
            os.environ['https_proxy'] = os.getenv("ProxyUrl")
            logger.info('  - 使用QL配置文件ProxyUrl代理：' + os.environ["ProxyUrl"])
        else:
            logger.info('  - 未使用代理，请确认当前网络环境可直连：api.openai.com')
    try:
        i = 1
        for ck in cks:        
            headers = {
                'cookie': ck.encode("utf-8"),
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.82 Safari/537.36',
                'Connection': 'keep-alive',
                'Cache-Control': 'max-age=0',
                'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="98", "Google Chrome";v="98"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'DNT': '1',
                'Upgrade-Insecure-Requests': '1',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                'Sec-Fetch-Site': 'same-site',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-User': '?1',
                'Sec-Fetch-Dest': 'document',
                'Referer': 'https://order.jd.com/',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept-Language': 'zh-CN,zh;q=0.9',
            }
            logger.debug('Builtin HTTP request header: %s', headers)
            logger.debug('Starting main processes')
            logger.info('\n开始第 '+ str(i) +' 个账号评价...\n')
            main(opts)
            i += 1
    # NOTE: It needs 3,000 times to raise this exception. Do you really want to
    # do like this?
    except RecursionError:
        logger.error("多次出现未完成情况，程序自动退出")
