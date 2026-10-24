# -*- coding: utf-8 -*-
"""
英语翻译助手 · 本地服务
=======================
基础工具 EnglishTranslator.html 可完全离线使用（逐行对照 + 点击取词）。

本服务为"导入自己的文档"提供增强：
  · 解析 PDF / DOCX / TXT 文档内容
  · 联网时自动翻译成中文（失败则仅显示英文，仍可点击取词）

启动：双击 启动工具(双击).bat  → 选 2
或    python server.py
然后浏览器打开 http://127.0.0.1:8338
"""
import io
import json
import os
import re
import sys
import time
import traceback
import zipfile
import urllib.request
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BASE = os.path.dirname(os.path.abspath(__file__))
HTML_FILE = os.path.join(BASE, 'EnglishTranslator.html')

# 让服务可以直接使用随工具附带的纯 Python 依赖（无需 pip 安装）
VENDOR = os.path.join(BASE, 'vendor')
if os.path.isdir(VENDOR) and VENDOR not in sys.path:
    sys.path.insert(0, VENDOR)

try:
    from pypdf import PdfReader
    HAVE_PYPDF = True
except Exception:
    HAVE_PYPDF = False


# ---------------- 文档解析 ----------------
def _clean_text(t: str) -> str:
    t = t.replace('\u2019', "'").replace('\u2018', "'")
    t = t.replace('\u201c', '"').replace('\u201d', '"')
    t = t.replace('\u00ad', '')
    t = t.replace('\ufffd', "'")
    return t


def extract_pdf(data: bytes) -> str:
    if not HAVE_PYPDF:
        raise RuntimeError('缺少 pypdf 组件（vendor/pypdf），无法解析 PDF')
    reader = PdfReader(io.BytesIO(data))
    parts = []
    for page in reader.pages:
        try:
            parts.append(page.extract_text() or '')
        except Exception:
            continue
    return '\n'.join(parts)


def extract_docx(data: bytes) -> str:
    """用标准库解析 .docx（本质是 zip + XML），逐段提取文本。"""
    import xml.etree.ElementTree as ET
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        try:
            xml = z.read('word/document.xml')
        except KeyError:
            return ''
    try:
        root = ET.fromstring(xml)
    except Exception:
        return ''
    ns = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
    paras = []
    for p in root.iter(ns + 'p'):
        pieces = [(t.text or '') for t in p.iter(ns + 't')]
        line = ''.join(pieces).strip()
        if line:
            paras.append(line)
    return '\n'.join(paras)


def decode_text(data: bytes) -> str:
    for enc in ('utf-8-sig', 'utf-8', 'gb18030', 'big5', 'latin-1'):
        try:
            return data.decode(enc)
        except Exception:
            continue
    return data.decode('utf-8', 'ignore')


def extract_document(data: bytes, ext: str) -> str:
    ext = (ext or '').lower().lstrip('.')
    if ext == 'pdf':
        text = extract_pdf(data)
    elif ext in ('docx',):
        text = extract_docx(data)
    elif ext in ('doc',):
        raise RuntimeError('旧版 .doc 暂不支持，请另存为 .docx 或 .pdf 后再导入')
    else:
        text = decode_text(data)
    return _clean_text(text or '')


# ---------------- 断句 ----------------
ABBREV = {'mr', 'mrs', 'ms', 'dr', 'prof', 'st', 'vs', 'etc', 'inc', 'ltd', 'jr', 'sr', 'no', 'fig', 'al'}
_END_RE = re.compile(r'[.?!。！？]["\'”’)]?\s*$')


def _clean_lines(text: str):
    """去掉 PDF 页眉/页码/来源标注等噪声行。"""
    out = []
    for raw in text.split('\n'):
        s = raw.strip()
        if not s:
            continue
        if re.match(r'^change\s+times', s, re.I):
            continue
        if re.match(r'^\d+$', s):
            continue
        if ('报刊来源' in s) or ('粉丝团' in s) or ('Addon' in s and '|' in s):
            continue
        if re.fullmatch(r'[\d\s.\-–—|]+', s):
            continue
        if len(s) <= 1:
            continue
        out.append(s)
    return out


CUE_WORDS = set('''of the a an to and or but in on at for with that which who whom whose from as by
is are was were has have had will would can could may might must not very more most
this these those their its our your his her my no nor so than then while when where'''.split())


def _should_join(buf: str, nxt: str) -> bool:
    """判断 PDF 的下一行是否应并入当前行（处理硬换行，同时避免粘连标题/副标题）。"""
    if _END_RE.search(buf):
        return False
    last = re.findall(r"[A-Za-z']+", buf)
    lastw = last[-1].lower() if last else ''
    if lastw in CUE_WORDS:
        return True
    if buf.rstrip()[-1:] in ',;:-–—':
        return True
    if not nxt:
        return False
    c = nxt[0]
    if not c.isalpha():      # 以标点/数字/引号开头 → 续行
        return True
    if c.islower():          # 以小写开头 → 续行
        return True
    return False             # 以大写字母开头且上一行非未完成 → 另起


def split_sentences(text: str):
    """先把 PDF 的硬换行拼回完整行，再按句末标点切句。"""
    lines = _clean_lines(text)
    # 1) 拼接硬换行
    joined = []
    buf = ''
    for ln in lines:
        if buf:
            if _should_join(buf, ln):
                buf = buf + ' ' + ln
            else:
                joined.append(buf)
                buf = ln
        else:
            buf = ln
    if buf:
        joined.append(buf)

    # 2) 按句末标点切句
    out = []
    for chunk in joined:
        parts = re.split(r'(?<=[.?!。！？])\s+(?=[A-Z0-9"\'“‘(])', chunk)
        for p in parts:
            p = p.strip()
            if not p:
                continue
            if not re.search(r'[A-Za-z]{2,}', p):
                continue
            if len(p) < 2:
                continue
            out.append(p)
    return out


# ---------------- 在线翻译（可选） ----------------
_CACHE = {}

_CJK_RE = re.compile(r'[\u4e00-\u9fff]')
_LATIN_RE = re.compile(r'[A-Za-z]')

def _clean_gloss(g: str) -> str:
    """保留干净的中文释义：必须含汉字、不含英文、去除拼音括号/噪声尾巴。"""
    if not g:
        return ''
    g = g.strip()
    if not _CJK_RE.search(g):
        return ''
    if _LATIN_RE.search(g):
        # 去掉 “xxx [da1]” 这类的拼音尾巴保留前面汉字
        g = re.split(r'\s*[\[【「]', g)[0].strip()
        if _LATIN_RE.search(g):
            return ''
    g = g.strip(' .。，,;；:：·~\u201c\u201d"\'')
    if len(g) < 1:
        return ''
    return g


def mymemory_glosses(word: str, max_g=6):
    """返回 MyMemory 提供的多个中文候选释义（去重、去噪声）。兜底用。"""
    out = []
    try:
        url = ('https://api.mymemory.translated.net/get?q=' +
               urllib.parse.quote(word) + '&langpair=en|zh-CN')
        with urllib.request.urlopen(url, timeout=5) as r:
            data = json.loads(r.read().decode('utf-8'))
        # 1) 主译文
        main = data.get('responseData') or {}
        mt = _clean_gloss(main.get('translatedText') or '')
        if mt:
            out.append(mt)
        # 2) 候选 matches
        for m in data.get('matches') or []:
            g = _clean_gloss(m.get('translation') or '')
            if g and g.lower() != word.lower() and g not in out:
                out.append(g)
            if len(out) >= max_g:
                break
    except Exception:
        pass
    return out


def dictapi_senses(word: str):
    """dictionaryapi.dev：结构化多义词条（音标 + 多义项 + 例句）。失败返回 []。"""
    for attempt in range(1):
        try:
            url = 'https://api.dictionaryapi.dev/api/v2/entries/en/' + urllib.parse.quote(word)
            with urllib.request.urlopen(url, timeout=4) as r:
                j = json.loads(r.read().decode('utf-8'))
            if not isinstance(j, list) or not j:
                return []
            e = j[0]
            ipa = (e.get('phonetic') or
                   next((p.get('text') for p in e.get('phonetics') or [] if p.get('text')), '') or '')
            senses = []
            seen = set()
            for m in e.get('meanings') or []:
                pos = m.get('partOfSpeech') or ''
                for d in m.get('definitions') or []:
                    en = (d.get('definition') or '').strip()
                    if not en:
                        continue
                    ex = (d.get('example') or '').strip()
                    key = (pos, en)
                    if key in seen:
                        continue
                    seen.add(key)
                    senses.append({'pos': pos, 'en': en, 'ex': ex})
            return {'ipa': ipa, 'senses': senses[:10]}
        except Exception:
            return []


def _strip_tags(s: str) -> str:
    s = str(s or '')
    s = re.sub(r'<[^>]+>', '', s)          # 去 HTML 标签
    s = s.replace('\u200b', '').strip()
    return s.strip()


def youdao_senses(word: str):
    """有道英汉词典：一次性给出多义项中文（<br/> 分隔一个义位的多个译法）。

    返回 {'ipa': '...', 'uk': '...', 'us': '...', 'senses': [ {'pos','zh','en','ex'} ... ]}
    任一失败返回 None。
    """
    try:
        url = 'https://dict.youdao.com/jsonapi?q=' + urllib.parse.quote(word)
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0',
            'Referer': 'https://dict.youdao.com/',
        })
        with urllib.request.urlopen(req, timeout=6) as r:
            j = json.loads(r.read().decode('utf-8'))
        ec = (j or {}).get('ec') or {}
        words = (ec.get('word')) or []
        if not words:
            return None
        w0 = words[0]
        ipa = _strip_tags(w0.get('phonetic') or '')
        uk = _strip_tags(w0.get('ukphone') or '')
        us = _strip_tags(w0.get('usphone') or '')
        senses = []
        seen = set()
        for tr in w0.get('trs') or []:
            for item in (tr.get('tr') or []):
                phrase = (item.get('l') or {}).get('i') or []
                if isinstance(phrase, list):
                    phrase = ' '.join(str(x) for x in phrase)
                text = _strip_tags(str(phrase))
                # 形如 “V. 拿，取；…” 或 “n. 熊；…”
                m = re.match(r'^([A-Za-z.,]+\s*\.)\s*(.*)$', text)
                if m:
                    pos, zh = m.group(1).strip(), m.group(2).strip()
                else:
                    pos, zh = '', text.strip()
                if not zh or zh in seen:
                    continue
                if any(c in zh for c in ('【', '人名', '地名')):
                    continue  # 跳过历史人名/地名词条，避免干扰
                seen.add(zh)
                senses.append({'pos': pos, 'zh': zh, 'en': '', 'ex': ''})
        if not senses:
            return None
        # 仅取常见词性（去重，保留 6 个）
        return {'ipa': ipa or (uk or us), 'uk': uk, 'us': us, 'senses': senses[:8]}
    except Exception:
        return None


def online_translate(text, target='zh-CN'):
    if text in _CACHE:
        return _CACHE[text]
    text = (text or '').strip()
    if not text:
        return ''
    # 1) MyMemory（响应快、无需注册）
    try:
        url = ('https://api.mymemory.translated.net/get?q=' +
               urllib.parse.quote(text) + '&langpair=en|zh-CN')
        with urllib.request.urlopen(url, timeout=6) as r:
            data = json.loads(r.read().decode('utf-8'))
            t = (data.get('responseData') or {}).get('translatedText')
            if t and 'MYMEMORY WARNING' not in t and 'QUERY LENGTH LIMIT' not in t:
                _CACHE[text] = t
                return t
    except Exception:
        pass
    # 2) LibreTranslate 公共实例（备选）
    for host in ('https://libretranslate.com', 'https://translate.terraprint.co'):
        try:
            payload = json.dumps({'q': text, 'source': 'en', 'target': 'zh'}).encode('utf-8')
            req = urllib.request.Request(host + '/translate', data=payload,
                                         headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(req, timeout=5) as r:
                data = json.loads(r.read().decode('utf-8'))
                if data.get('translatedText'):
                    _CACHE[text] = data['translatedText']
                    return data['translatedText']
        except Exception:
            continue
    _CACHE[text] = ''
    return ''


# ---------------- HTTP ----------------
class Handler(BaseHTTPRequestHandler):
    server_version = 'EngTrans/2.0'

    def _cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Access-Control-Allow-Private-Network', 'true')

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        path = self.path.split('?')[0]
        if path in ('/', '/index.html'):
            if not os.path.exists(HTML_FILE):
                return self._send_html('<h1>未找到 EnglishTranslator.html</h1>')
            with open(HTML_FILE, 'rb') as f:
                data = f.read()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(data)))
            self._cors()
            self.end_headers()
            self.wfile.write(data)
        elif path == '/api/ping':
            self._json({'ok': True, 'pypdf': HAVE_PYPDF})
        elif path == '/api/word':
            try:
                parsed = urllib.parse.urlparse(self.path)
                qs = urllib.parse.parse_qs(parsed.query)
                w = (qs.get('w', [''])[0] or '').strip()
                if not w:
                    return self._json({'ok': False, 'error': 'no word'})
                # 多义词条：优选 有道(Youdao 英汉牛津风多义), 兜底 MyMemory + dictapi
                yd = youdao_senses(w)
                senses = []
                ipa = ''
                if yd and yd.get('senses'):
                    ipa = yd.get('us') or yd.get('uk') or yd.get('ipa') or ''
                    senses = yd['senses']
                else:
                    glosses = mymemory_glosses(w)
                    dd = dictapi_senses(w)
                    if not isinstance(dd, dict):
                        dd = {}
                    seen = set()
                    for g in glosses:
                        if g in seen:
                            continue
                        seen.add(g)
                        senses.append({'zh': g, 'pos': '', 'en': ''})
                    for s in (dd.get('senses') or []):
                        mark = s.get('en') or ''
                        if mark and mark in seen:
                            continue
                        if mark:
                            seen.add(mark)
                        senses.append({'zh': '', 'pos': s.get('pos', ''), 'en': s.get('en', '')})
                    ipa = (dd or {}).get('ipa', '')
                if not senses:
                    # 退化为普通整句/整词翻译
                    zh = online_translate(w)
                    if zh:
                        senses = [{'zh': zh, 'pos': '', 'en': ''}]
                return self._json({'ok': True, 'word': w,
                                   'ipa': ipa or '',
                                   'senses': senses,
                                   'source': 'youdao' if yd else ('mymemory' if not yd else '')})
            except Exception as e:
                traceback.print_exc()
                return self._json({'ok': False, 'error': str(e)})
        else:
            self.send_error(404)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path, qs = parsed.path, urllib.parse.parse_qs(parsed.query)
        try:
            if path == '/api/import':
                return self._handle_import(qs)
            if path == '/api/translate':
                return self._handle_translate()
            if path == '/api/translate-lines':
                return self._handle_translate_lines()
        except Exception as e:
            return self._json({'ok': False, 'error': str(e)})
        self.send_error(404)

    def _read_body(self) -> bytes:
        length = int(self.headers.get('Content-Length') or 0)
        return self.rfile.read(length) if length else b''

    def _handle_import(self, qs):
        ext = (qs.get('ext', ['txt'])[0] or 'txt')
        want_tr = (qs.get('translate', ['0'])[0] == '1')
        data = self._read_body()
        if not data:
            return self._json({'ok': False, 'error': '空文件'})
        text = extract_document(data, ext)
        sents = split_sentences(text)
        if len(sents) > 400:
            sents = sents[:400]
        entries = []
        for s in sents:
            zh = online_translate(s) if want_tr else ''
            entries.append({'en': s, 'zh': zh})
        return self._json({'ok': True, 'entries': entries,
                           'chars': len(text), 'sentences': len(entries),
                           'translated': sum(1 for e in entries if e['zh'])})

    def _handle_translate(self):
        body = json.loads(self._read_body().decode('utf-8'))
        text = body.get('text', '')
        sents = split_sentences(text) if '\n' in text else [text]
        entries = [{'en': s, 'zh': online_translate(s)} for s in sents if s.strip()]
        return self._json({'ok': True, 'entries': entries})

    def _handle_translate_lines(self):
        """批量翻译若干行；带总时限，超时就返回空串（前端保留英文）。"""
        body = json.loads(self._read_body().decode('utf-8'))
        lines = body.get('lines') or []
        lines = [str(x) for x in lines][:60]
        deadline = time.time() + 40
        zh = []
        for s in lines:
            if time.time() > deadline:
                zh.append('')
                continue
            zh.append(online_translate(s) if s.strip() else '')
        return self._json({'ok': True, 'zh': zh})

    def _send_html(self, html):
        data = html.encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _json(self, obj):
        data = json.dumps(obj, ensure_ascii=False).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self._cors()
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *a):
        pass


def main():
    port = 8338
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            port = 8338
    try:
        srv = ThreadingHTTPServer(('127.0.0.1', port), Handler)
    except OSError:
        srv = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        port = srv.server_address[1]
    # 把实际端口写给启动器，便于自动打开正确地址
    try:
        with open(os.path.join(BASE, '_port.txt'), 'w', encoding='utf-8') as f:
            f.write(str(port))
    except Exception:
        pass
    print('=' * 56)
    print('  英语翻译助手 · 本地服务已启动')
    print(f'  请在浏览器打开:  http://127.0.0.1:{port}')
    print(f'  PDF 解析组件: {"可用" if HAVE_PYPDF else "不可用（vendor/pypdf 缺失）"}')
    print('  提示：内置文章可离线使用；导入新文档时若联网会自动翻译。')
    print('  关闭此窗口即停止服务。')
    print('=' * 56)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        srv.shutdown()
    finally:
        try:
            os.remove(os.path.join(BASE, '_port.txt'))
        except Exception:
            pass


if __name__ == '__main__':
    main()