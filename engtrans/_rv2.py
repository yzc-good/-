import urllib.request, json, hashlib, time
def get(u, raw=False, tries=3):
    last=None
    for i in range(tries):
        try:
            req=urllib.request.Request(u, headers={'User-Agent':'Mozilla/5.0',
                'Cache-Control':'no-cache','Pragma':'no-cache'})
            d=urllib.request.urlopen(req, timeout=45).read()
            return d if raw else d.decode('utf-8','ignore')
        except Exception as e:
            last=e; time.sleep(2)
    raise last

ts=str(int(time.time()))
cands=[
 'https://raw.githubusercontent.com/yzc-good/-/main/update/update.json?v='+ts,
 'https://ghproxy.net/https://raw.githubusercontent.com/yzc-good/-/main/update/update.json?v='+ts,
 'https://ghfast.top/https://raw.githubusercontent.com/yzc-good/-/main/update/update.json?v='+ts,
]
print('=== 远端 update.json（多镜像重试）===')
ok=None
for u in cands:
    try:
        m=json.loads(get(u)); a=m['android']; f=a['files'][0]
        print('  OK %-14s webVersion=%s type=%s file=%s size=%s' % (u.split('/')[2][:14], a.get('webVersion'), a.get('type'), f['name'], f['size']))
        if a.get('webVersion')==10: ok=f
    except Exception as e:
        print('  ERR %-14s %s' % (u.split('/')[2][:14], str(e)[:50]))

if ok:
    print()
    print('=== 远端 web-10.zip 校验 ===')
    local_sha='3a80e17e55ae0d04567a3a8fdde3f733f19fa2171cfeb0b3e435507ce8942d4b'
    for base in ['https://raw.githubusercontent.com/yzc-good/-/main/update/',
                 'https://ghproxy.net/https://raw.githubusercontent.com/yzc-good/-/main/update/']:
        try:
            d=get(base+'web-10.zip?v='+ts, raw=True)
            h=hashlib.sha256(d).hexdigest()
            print('  %-14s %d bytes  sha256 %s' % (base.split('/')[2][:14], len(d), '一致 ✅' if h==local_sha else '不一致 '+h[:16]))
            break
        except Exception as e:
            print('  ERR %-14s %s' % (base.split('/')[2][:14], str(e)[:50]))
