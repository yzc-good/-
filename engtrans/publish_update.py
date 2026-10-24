# -*- coding: utf-8 -*-
"""
发布脚本：生成“远程更新”所需的文件，上传到你的 GitHub 仓库即可让平板自动更新。

产物目录：<BASE>/publish_update/
  ├─ update.json        ← 更新清单（更新入口）
  ├─ web-<n>.zip        ← 网页内容包（热更新用；内含 index.html 等）
  └─ EnglishTranslator-vX.Y.apk  ← 整包升级 APK（可选，拷入即可）

使用步骤（每次要发布新版本时）：
  1) 先在 build_mobile.py 重建好 mobile/www/index.html（见下），再构建并签名好新版 APK。
  2) 运行本脚本：
        python publish_update.py
    它是交互式的，会问你这次发布“网页热更新”还是“整包升级”或两者。
  3) 把 publish_update/ 下所有文件上传到仓库 update/ 目录：
        https://github.com/yzc-good/- 的 update/ 目录
    最终能通过这两个地址访问到：
        https://raw.githubusercontent.com/yzc-good/-/main/update/update.json
        https://raw.githubusercontent.com/yzc-good/-/main/update/web-<n>.zip
  4) 平板上点“更新”即可检测到并下载。

数据文件始终放 D 盘（本目录），符合要求。
"""
import hashlib, json, os, shutil, sys, zipfile

BASE = os.path.dirname(os.path.abspath(__file__))
MOBILE = os.path.join(BASE, 'mobile')
WWW = os.path.join(MOBILE, 'www')
OUT = os.path.join(BASE, 'publish_update')

# 远端基础地址（与 App 内置 DEFAULT_MANIFEST_URL 对应）
RAW_BASE = 'https://raw.githubusercontent.com/yzc-good/-/main/update'


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()


def size(path):
    return os.path.getsize(path)


def zip_www(version_int):
    """把 mobile/www 打成 web-<n>.zip，index.html 存根在最外层。"""
    os.makedirs(OUT, exist_ok=True)
    name = 'web-%d.zip' % version_int
    out = os.path.join(OUT, name)
    if not os.path.exists(os.path.join(WWW, 'index.html')):
        raise SystemExit('缺少 ' + os.path.join(WWW, 'index.html') + '，请先运行 build_mobile.py')
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(WWW):
            for f in files:
                full = os.path.join(root, f)
                rel = os.path.relpath(full, WWW).replace('\\', '/')
                z.write(full, rel)
    print('已生成内容包：', out, size(out), 'bytes')
    return out, name


def build_manifest(remote_web, web_zip_name, apk_path=None, apk_version_name=None, apk_version_code=None):
    """构造 update.json。webVersion 每次+1；若带 apk 则同时整包升级。"""
    files = []
    if web_zip_name:
        zp = os.path.join(OUT, web_zip_name)
        files.append({
            'name': web_zip_name,
            'url': RAW_BASE + '/' + web_zip_name,
            'size': size(zp),
            'sha256': sha256(zp),
        })
    manifest = {'android': {}}
    if files:
        manifest['android']['webVersion'] = remote_web
    apk = None
    if apk_path:
        apk = {
            'url': RAW_BASE + '/' + os.path.basename(apk_path),
            'versionName': apk_version_name,
            'versionCode': apk_version_code,
            'size': size(apk_path),
            'sha256': sha256(apk_path),
        }
    if apk:
        # 整包升级时 type 为 both（Apk下载优先）
        pass
    if apk and files:
        manifest['android']['type'] = 'both'
    elif apk and not files:
        manifest['android']['type'] = 'apk'
    elif files:
        manifest['android']['type'] = 'web'
    if apk:
        manifest['android']['apk'] = apk
    manifest['android']['files'] = files
    return manifest


def main():
    print('发布目录：', OUT)
    os.makedirs(OUT, exist_ok=True)

    # 1) 问：这次发布什么
    print('可选更新类型：')
    print('  [1] 仅网页内容热更新（推荐日常用）')
    print('  [2] 仅 App 整包升级')
    print('  [3] 两者都要')
    choice = input('请输入编号（默认 1）：').strip() or '1'

    do_web = choice in ('1', '3')
    do_apk = choice in ('2', '3')

    remote_web = 0
    web_zip_name = None

    if do_web:
        # 2) 当前 web 版本号：读上次发布记录
        st = os.path.join(OUT, '.version')
        last = 0
        if os.path.exists(st):
            try:
                with open(st, encoding='utf-8') as f:
                    last = int(json.load(f).get('webVersion', 0))
            except Exception:
                last = 0
        remote_web = last + 1
        web_zip, web_zip_name = zip_www(remote_web)

    apk_path = None
    apk_vn = None
    apk_vc = None
    if do_apk:
        # 3) 找已签名 APK：优先 D 盘根的 EnglishTranslator-vX.Y.apk 或用户指定
        cands = []
        for fn in os.listdir(BASE):
            if fn.endswith('.apk') and not fn.endswith('-unsigned.apk'):
                cands.append(os.path.join(BASE, fn))
        cands.sort()
        if cands:
            print('找到已签名 APK（取最新）：')
            for i, c in enumerate(cands):
                print('  [%d] %s' % (i, os.path.basename(c)))
            idx = input('选择（默认最新 %d）：' % (len(cands) - 1)).strip()
            sel = cands[int(idx)] if idx.isdigit() and 0 <= int(idx) < len(cands) else cands[-1]
        else:
            print('未在发布目录下找到已签名 APK（EnglishTranslator-v*.apk）。')
            sel = input('请输入 APK 完整路径：').strip()
        apk_path = sel
        vn = input('请输入应用版本名（如 1.2）：').strip() or '1.2'
        vc = input('请输入应用版本号（整数，须 > 上一个）：').strip()
        apk_vn = vn
        apk_vc = int(vc) if vc.isdigit() else 2

        # 拷贝到发布目录
        dst = os.path.join(OUT, os.path.basename(apk_path))
        shutil.copyfile(apk_path, dst)
        print('已拷贝 APK 到发布目录：', dst)
        apk_path = dst

    manifest = build_manifest(remote_web, web_zip_name, apk_path, apk_vn, apk_vc)
    with open(os.path.join(OUT, 'update.json'), 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print('已生成 update.json：\n', json.dumps(manifest, ensure_ascii=False, indent=2))

    # 记录本次 web 版本，供下次自增
    with open(os.path.join(OUT, '.version'), 'w', encoding='utf-8') as f:
        json.dump({'webVersion': remote_web}, f)

    print('\n==== 发布成功 ====')
    print('请把以下文件上传到仓库 update/ 目录：')
    print('  https://github.com/yzc-good/-  →  新建/上传到 update/')
    for fn in os.listdir(OUT):
        p = os.path.join(OUT, fn)
        if os.path.isfile(p):
            print('    -', fn, '(%d KB)' % (size(p) // 1024))
    print('\n上传后检查：')
    print('  ' + RAW_BASE + '/update.json')


if __name__ == '__main__':
    main()