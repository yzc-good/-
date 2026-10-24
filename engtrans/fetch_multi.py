# -*- coding: utf-8 -*-
"""一次性脚本：为本地词库所有词抓取有道多义词义，生成 data/dict_multi.json 缓存。

可断点续跑：已抓取的词直接跳过。
"""
import json, os, sys, re, glob, time, concurrent.futures

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import server  # 复用 youdao_senses / _strip_tags

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, 'data', 'dict_multi.json')


def collect_words():
    words = {}
    for p in glob.glob(os.path.join(BASE, 'data', 'exam_*.txt')):
        for raw in open(p, encoding='utf-8-sig'):
            line = raw.strip().lstrip('\ufeff')
            if not line or line.startswith('#'):
                continue
            parts = line.split('~')
            if len(parts) < 3:
                continue
            w = parts[0].strip().lstrip('\ufeff').lower()
            if re.match(r"^[a-z][a-z'\- ]*$", w):
                words.setdefault(w, w)
    for n in ['dictionary.json', 'dictionary_extra.json', 'dictionary_names.json']:
        p = os.path.join(BASE, 'data', n)
        if os.path.exists(p):
            d = json.load(open(p, encoding='utf-8'))
            for k in d:
                if re.match(r"^[a-z][a-z'\- ]*$", k.lower()):
                    words.setdefault(k.lower(), k)
    return list(words.keys())


def main():
    words = collect_words()
    print('total words:', len(words))
    # load existing cache
    done = {}
    if os.path.exists(OUT):
        done = json.load(open(OUT, encoding='utf-8'))
    remain = [w for w in words if w not in done]
    print('remaining:', len(remain))
    if not remain:
        print('already up to date'); return

    stats = {'ok': 0, 'fail': 0}

    def fetch(w):
        try:
            yd = server.youdao_senses(w)
            if yd and yd.get('senses'):
                return w, {'headword': w, 'ipa': (yd.get('us') or yd.get('uk') or ''),
                           'pos': [s['pos'] for s in yd['senses']],
                           'meanings': [{'zh': s['zh'], 'pos': s.get('pos','')} for s in yd['senses']]}
            return w, None
        except Exception:
            return w, None

    t0 = time.time()
    n = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
        for w, val in ex.map(fetch, remain):
            if val:
                done[w] = val
                stats['ok'] += 1
            else:
                stats['fail'] += 1
            n += 1
            if n % 250 == 0:
                with open(OUT, 'w', encoding='utf-8') as f:
                    json.dump(done, f, ensure_ascii=False)
                el = time.time() - t0
                print(f'  {n}/{len(remain)} ok={stats["ok"]} fail={stats["fail"]} '
                      f'eta={el/n*(len(remain)-n):.0f}s', flush=True)
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(done, f, ensure_ascii=False)
    print('done. ok=%d fail=%d saved=%d elapsed=%.0fs' %
          (stats['ok'], stats['fail'], len(done), time.time() - t0))


if __name__ == '__main__':
    main()