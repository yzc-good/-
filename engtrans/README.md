# 英语翻译助手（English Translator）

一个**离线优先**的英语阅读辅助工具：逐行对照翻译 + 点击取词，支持本地解析 PDF / Word。
有网页版（单文件）和安卓 / 鸿蒙平板版（独立 App，不用开电脑）。

## 功能

- **逐行对照翻译**：一行原文、一行译文，适合精读外刊
- **中英双向互译**：导入英文文档出中文，导入中文文档出英文，逐行自动识别方向
- **点击取词**：点任意英文单词，右侧弹出音标 / 词性分组释义 / 例句 / 同反义词
- **离线词库**：内置约 6200 个词条（含一词多义）+ 4 万余条词形变化
- **本地文档解析**：PDF / DOCX / TXT / MD 都在设备本地解析，不上传服务器
- **联网增强**（可选）：查未收录词、整句自动翻译
- **App 内远程更新**：热更新网页内容，或整包升级（见 `update/` 目录）

## 目录说明

```
engtrans/
├─ EnglishTranslator.html      网页版单文件成品（内置词库，双击可用）
├─ template.html               网页版模板（源码，改这个再重新构建）
├─ build_html.py               构建网页版：模板 + data/ → EnglishTranslator.html
├─ server.py / server.pyw      本地服务（网页版用它解析 PDF、联网翻译）
├─ 启动工具(双击).bat           网页版一键启动器
├─ data/                       词库与双语数据（txt + json）
├─ vendor/                     随附 PDF 解析组件（pypdf）
├─ validate.js                 检查构建产物里的 JS 语法
├─ publish_update.py           生成远程更新包（update.json + web-*.zip）
├─ 使用说明.txt                 面向使用者的说明
├─ 发版操作清单.txt             面向维护者的发版步骤
└─ mobile/                     安卓 / 鸿蒙平板版（Capacitor 工程）
   ├─ template.mobile.html     移动端模板（源码）
   ├─ build_mobile.py          构建：模板 + data/ → mobile/www/index.html
   ├─ www/                     构建产物（被 Capacitor 打包进 App）
   ├─ capacitor.config.json
   └─ android/
      └─ app/src/main/java/com/engtrans/app/
         ├─ MainActivity.java   注册插件
         └─ UpdateManager.java  远程更新插件（多镜像 / 校验 / 热更新 / 整包升级）
```

## 网页版怎么用

```bash
python build_html.py          # 生成 EnglishTranslator.html
python server.py             # 启动本地服务（解析 PDF / 联网翻译）
```

也可直接双击 `EnglishTranslator.html` 离线阅读（PDF 导入需先启服务）。

## 平板版怎么构建

需要 JDK 21、Android SDK、Gradle（体积大，**未包含在本仓库中**，请自行安装）。

```bash
python build_mobile.py                                   # 1. 生成 mobile/www/index.html
cd mobile
node node_modules/@capacitor/cli/bin/capacitor sync android   # 2. 同步进 Android 工程
cd android
gradlew.bat assembleRelease                              # 3. 构建
```

签名（密钥请自行生成，**不要提交**）：

```bash
apksigner sign --ks <你的.keystore> --ks-key-alias <别名> \
  --out EnglishTranslator.apk app/build/outputs/apk/release/app-release-unsigned.apk
```

## 发布一次远程更新

```bash
python publish_update.py      # 选择：仅网页 / 仅整包 / 两者
```

把生成的 `publish_update/` 下文件传到本仓库 `update/` 目录，App 内点「🔄 更新」即可收到。
详细步骤见 `发版操作清单.txt`。

App 默认读取的清单地址：

```
https://raw.githubusercontent.com/yzc-good/-/main/update/update.json
```

国内网络访问 GitHub raw 不稳定，App 内置了多镜像回退（ghfast.top / ghproxy.net / jsDelivr），
哪个先通用哪个，无需额外配置。

## 数据来源与授权

- `data/` 下的词库为本项目整理，**使用或再分发前请确认每个文件的来源与授权**。
- 内置阅读文章来自公开报道，仅作阅读练习示例。
- 联网查词 / 翻译会调用第三方接口，使用前请遵守对应服务条款。

## 声明

本项目为个人学习与自用工具，非商业产品。
