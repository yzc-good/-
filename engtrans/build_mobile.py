# -*- coding: utf-8 -*-
"""生成独家 Android App 用的 www/index.html：复用 build_html.py 的数据装配。"""
import json, os, sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)
MOBILE = os.path.join(BASE, 'mobile')
sys.path.insert(0, ROOT)
import build_html  # 复用数据装配（bilingual/dic/inflect/funcWords/index_word）

payload = build_html.build_payload()

with open(os.path.join(MOBILE, 'template.mobile.html'), encoding='utf-8') as f:
    html = f.read()

html = html.replace('/*__DATA__*/', 'window.APP_DATA = ' + json.dumps(payload, ensure_ascii=False) + ';')

out = os.path.join(MOBILE, 'www', 'index.html')
with open(out, 'w', encoding='utf-8') as f:
    f.write(html)
print('written', out, os.path.getsize(out), 'bytes')