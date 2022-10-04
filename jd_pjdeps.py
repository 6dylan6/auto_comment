# -*- coding: utf-8 -*-

'''
new Env('评价依赖安装');
8 8 2 10 * https://raw.githubusercontent.com/6dylan6/auto_comment/main/jd_pjdeps.py
'''

import os
from time import sleep
print('第一次运行评价出错才运行此程序，如果没有问题请勿运行，以免弄出问题!!!')
sleep(2)
print('10s后开始安装依赖......')
sleep(10)
os.system('apk add --no-cache libxml2-dev libxslt-dev')
os.system('pip install -U --force-reinstall pip')
os.system('pip3 install lxml')