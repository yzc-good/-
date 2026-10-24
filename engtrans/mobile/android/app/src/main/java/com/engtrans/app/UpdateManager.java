package com.engtrans.app;

import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.Build;

import androidx.core.content.FileProvider;

import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.BufferedInputStream;
import java.io.BufferedOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.CancellationException;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.zip.ZipEntry;
import java.util.zip.ZipFile;

/**
 * 远程更新插件。
 *
 * 由于国内网络访问 GitHub raw 经常超时/被阻断，这里同时向多个地址
 * （GitHub raw 官方 + 公共 CDN 镜像）并发请求 update.json，
 * 谁先成功就用谁，后续的内容包 / APK 也从那个镜像下载。
 */
@CapacitorPlugin(name = "UpdateManager")
public class UpdateManager extends Plugin {

    private static final String DIR_UPDATES = "updates";
    private static final String DIR_WEB = "www";

    /**
     * 更新清单地址 + 该镜像对应的文件下载基准目录 + 是否只作兜底。
     *
     * 只使用「raw 的直通代理」：它们每次都回源，不会返回陈旧内容。
     * 曾经用过 jsDelivr，但它对分支有最长 7 天的缓存且加时间戳也绕不过，
     * 导致「检查说有新版、下载时却说清单里没有 apk」，已移除。
     */
    private static final String[][] MIRRORS = {
            // { manifestUrl, filesBase, preferLast(1=只在前面的都失败时才用) }
            {"https://raw.githubusercontent.com/yzc-good/-/main/update/update.json",
             "https://raw.githubusercontent.com/yzc-good/-/main/update/", "0"},
            {"https://ghfast.top/https://raw.githubusercontent.com/yzc-good/-/main/update/update.json",
             "https://ghfast.top/https://raw.githubusercontent.com/yzc-good/-/main/update/", "0"},
            {"https://ghproxy.net/https://raw.githubusercontent.com/yzc-good/-/main/update/update.json",
             "https://ghproxy.net/https://raw.githubusercontent.com/yzc-good/-/main/update/", "0"},
            {"https://gh-proxy.com/https://raw.githubusercontent.com/yzc-good/-/main/update/update.json",
             "https://gh-proxy.com/https://raw.githubusercontent.com/yzc-good/-/main/update/", "0"},
    };

    private static final int MANIFEST_TOTAL_TIMEOUT_MS = 25000;
    /** 兜底镜像已拿到后，最多再等其他地址这么久 */
    private static final int FALLBACK_GRACE_MS = 12000;

    /**
     * 「检查」拿到的清单缓存：用户点完检查再点下载时直接复用，
     * 避免第二次请求命中别的镜像、出现「检查有包、下载没包」的不一致。
     * 每次主动「检查更新」都会重新拉取，所以不会漏掉新版本。
     */
    private static final long MANIFEST_CACHE_TTL_MS = 10 * 60 * 1000L;
    private Manifest cachedManifest;
    private long cachedManifestAt = 0L;

    private void remember(Manifest m) {
        if (m == null) return;
        cachedManifest = m;
        cachedManifestAt = System.currentTimeMillis();
    }

    // ---------------------------------------------------------------
    // 检查更新
    // ---------------------------------------------------------------
    @PluginMethod
    public void check(PluginCall call) {
        try {
            int webVersion = getLocalWebVersion();
            int appVersionCode = currentVersionCode();

            // 主动检查一律重新拉取（不复用缓存），确保能发现刚发布的新版本
            Manifest m = fetchManifest(call.getString("manifestUrl", null), false);
            JSONObject android = m.json.optJSONObject("android");
            if (android == null) {
                call.resolve(reply("none", "清单中没有 android 更新信息",
                        webVersion, appVersionCode, "", false, m.host));
                return;
            }
            int remoteWeb = android.optInt("webVersion", 0);
            String updateType = android.optString("type", "web");
            JSONObject apkObj = android.optJSONObject("apk");
            String apkVersionName = (apkObj != null) ? apkObj.optString("versionName", "") : "";
            int apkVersionCode = (apkObj != null) ? apkObj.optInt("versionCode", 0) : 0;

            boolean apkUpdate = apkVersionCode > appVersionCode;
            boolean webUpdate = (updateType.equals("web") || updateType.equals("both")) && remoteWeb > webVersion;

            if (!apkUpdate && !webUpdate) {
                call.resolve(reply("none",
                        "已是最新版本（网页 v" + webVersion + "，App " + currentVersionName() + "）",
                        webVersion, appVersionCode, apkVersionName, false, m.host));
                return;
            }
            String msg;
            if (apkUpdate && webUpdate) {
                msg = "发现新版本：网页 v" + remoteWeb + "，且 App 可升级到 " + apkVersionName;
            } else if (webUpdate) {
                msg = "发现应用内容更新：网页 v" + remoteWeb;
            } else {
                msg = "发现新版 App：" + apkVersionName;
            }
            call.resolve(reply("available", msg, webVersion, appVersionCode,
                    apkVersionName, apkUpdate, m.host));
        } catch (Exception e) {
            call.reject("检查更新失败：" + describe(e), "CHECK_ERR");
        }
    }

    // ---------------------------------------------------------------
    // 下载并应用网页内容热更新
    // ---------------------------------------------------------------
    @PluginMethod
    public void applyWeb(PluginCall call) {
        try {
            Manifest m = fetchManifest(call.getString("manifestUrl", null), true);
            JSONObject android = m.json.optJSONObject("android");
            if (android == null) {
                call.reject("清单里没有 android 信息", "NO_MANIFEST");
                return;
            }
            int remoteWeb = android.optInt("webVersion", 0);

            // 保险：绝不应用不比当前更旧的内容，避免"降级"
            int localWeb = getLocalWebVersion();
            if (remoteWeb > 0 && remoteWeb <= localWeb) {
                JSObject ret = new JSObject();
                ret.put("ok", false);
                ret.put("skipped", true);
                ret.put("webVersion", localWeb);
                ret.put("message", "当前已是最新内容（v" + localWeb + "），无需更新");
                call.resolve(ret);
                return;
            }

            JSONArray files = android.optJSONArray("files");
            if (files == null || files.length() == 0) {
                call.reject("清单缺少内容包 files", "NO_FILES");
                return;
            }
            JSONObject f = files.getJSONObject(0);

            File webDir = getWebDir();
            File tmpDir = new File(getContext().getFilesDir(), DIR_WEB + "_new");
            if (tmpDir.exists()) deleteRecursive(tmpDir);
            if (!tmpDir.mkdirs()) {
                call.reject("无法创建临时目录", "IO_ERR");
                return;
            }

            File zipFile = download(remoteFileUrl(m, f, "web.zip"),
                    new File(getContext().getFilesDir(), DIR_UPDATES + "/web.zip"), 90000);
            String expectedSha = f.optString("sha256", "");
            if (!expectedSha.isEmpty() && !sha256(zipFile).equalsIgnoreCase(expectedSha)) {
                call.reject("内容包校验失败（sha256 不匹配）", "CHECKSUM");
                return;
            }
            unzip(zipFile, tmpDir);
            zipFile.delete();

            // 安全检查：必须有 index.html，否则不替换现有内容
            if (!new File(tmpDir, "index.html").isFile()) {
                deleteRecursive(tmpDir);
                call.reject("内容包不完整（缺少 index.html）", "BAD_PACKAGE");
                return;
            }
            writeVersion(tmpDir, remoteWeb);

            // 原子替换：先删旧目录，再把新目录改名过去
            if (webDir.exists()) deleteRecursive(webDir);
            if (!tmpDir.renameTo(webDir)) {
                deleteRecursive(tmpDir);
                call.reject("启用新内容失败（无法替换目录）", "IO_ERR");
                return;
            }

            persistTo(webDir.getAbsolutePath());
            bridge.setServerBasePath(webDir.getAbsolutePath());

            JSObject ret = new JSObject();
            ret.put("ok", true);
            ret.put("webVersion", remoteWeb);
            ret.put("path", webDir.getAbsolutePath());
            ret.put("source", m.host);
            call.resolve(ret);
        } catch (Exception e) {
            call.reject("应用内容更新失败：" + describe(e), "APPLY_ERR");
        }
    }

    // ---------------------------------------------------------------
    // 下载 APK 并触发系统安装
    // ---------------------------------------------------------------
    @PluginMethod
    public void installApp(PluginCall call) {
        try {
            // 优先复用「检查」时的清单；若里面没有 apk，强制重新拉一次再判断
            Manifest m = fetchManifest(call.getString("manifestUrl", null), true);
            JSONObject android = m.json.optJSONObject("android");
            if (android == null || !android.has("apk")) {
                m = fetchManifest(call.getString("manifestUrl", null), false);
                android = m.json.optJSONObject("android");
            }
            if (android == null || !android.has("apk")) {
                call.reject("清单里没有整包升级信息，请重新点「更新」再试", "NO_APK");
                return;
            }
            JSONObject apk = android.getJSONObject("apk");
            File apkFile = download(remoteFileUrl(m, apk, "app.apk"),
                    new File(getContext().getFilesDir(), DIR_UPDATES + "/app.apk"), 180000);
            String expectedSha = apk.optString("sha256", "");
            if (!expectedSha.isEmpty() && !sha256(apkFile).equalsIgnoreCase(expectedSha)) {
                call.reject("APK 校验失败（sha256 不匹配）", "CHECKSUM");
                return;
            }
            promptInstall(apkFile);
            JSObject ret = new JSObject();
            ret.put("ok", true);
            ret.put("pending", true);
            ret.put("source", m.host);
            call.resolve(ret);
        } catch (Exception e) {
            call.reject("下载新版 App 失败：" + describe(e), "INSTALL_ERR");
        }
    }

    // ---------------------------------------------------------------
    // 本地状态
    // ---------------------------------------------------------------
    @PluginMethod
    public void status(PluginCall call) {
        JSObject ret = new JSObject();
        ret.put("appVersionName", currentVersionName());
        ret.put("appVersionCode", currentVersionCode());
        ret.put("webVersion", getLocalWebVersion());
        ret.put("webPath", getWebDir().getAbsolutePath());
        ret.put("manifestUrl", MIRRORS[0][0]);
        JSONArray mirrors = new JSONArray();
        for (String[] mir : MIRRORS) mirrors.put(mir[0]);
        ret.put("mirrors", mirrors);
        call.resolve(ret);
    }

    // ---------------------------------------------------------------
    // 清单获取：多镜像并发，取最快成功的那个
    // ---------------------------------------------------------------
    private static class Manifest {
        JSONObject json;
        String filesBase;
        String host;
    }

    private Manifest fetchManifest(String overrideUrl, boolean allowCache) throws Exception {
        // 调用方指定了地址就只用它
        if (overrideUrl != null && !overrideUrl.trim().isEmpty()) {
            overrideUrl = overrideUrl.trim();
            Manifest m = new Manifest();
            m.json = fetchJson(overrideUrl, 20000);
            m.filesBase = overrideUrl.substring(0, overrideUrl.lastIndexOf('/') + 1);
            m.host = hostOf(overrideUrl);
            return m;
        }

        // 复用「检查」时拿到的清单，保证后续动作与用户看到的完全一致
        if (allowCache && cachedManifest != null
                && System.currentTimeMillis() - cachedManifestAt < MANIFEST_CACHE_TTL_MS) {
            return cachedManifest;
        }

        ExecutorService pool = Executors.newFixedThreadPool(MIRRORS.length);
        final List<Future<Object[]>> futures = new ArrayList<>();
        try {
            for (final String[] mir : MIRRORS) {
                futures.add(pool.submit(() -> {
                    JSONObject j = fetchJson(mir[0], 20000);
                    return new Object[]{j, mir[1], hostOf(mir[0])};
                }));
            }

            boolean[] handled = new boolean[futures.size()];
            List<String> errors = new ArrayList<>();
            Manifest fallback = null;   // 来自"仅兜底"镜像的结果
            long startAt = System.currentTimeMillis();
            long deadline = startAt + MANIFEST_TOTAL_TIMEOUT_MS;

            while (System.currentTimeMillis() < deadline) {
                boolean allHandled = true;
                for (int i = 0; i < futures.size(); i++) {
                    if (handled[i]) continue;
                    allHandled = false;
                    Future<Object[]> f = futures.get(i);
                    if (!f.isDone()) continue;
                    handled[i] = true;
                    try {
                        Object[] r = f.get();
                        Manifest m = new Manifest();
                        m.json = (JSONObject) r[0];
                        m.filesBase = (String) r[1];
                        m.host = (String) r[2];
                        if ("1".equals(MIRRORS[i][2])) {
                            if (fallback == null) fallback = m;
                        } else {
                            remember(m);
                            return m;   // 优先镜像，立刻采用
                        }
                    } catch (ExecutionException ee) {
                        errors.add(hostOf(MIRRORS[i][0]) + ": " + describe(ee.getCause()));
                    } catch (CancellationException ce) {
                        errors.add(hostOf(MIRRORS[i][0]) + ": 已取消");
                    }
                }
                if (allHandled) break;
                // 兜底镜像已就绪时，不必死等其他地址全部超时
                if (fallback != null && System.currentTimeMillis() - startAt >= FALLBACK_GRACE_MS) break;
                Thread.sleep(120);
            }
            if (fallback != null) { remember(fallback); return fallback; }
            if (errors.isEmpty()) errors.add("全部超时（" + (MANIFEST_TOTAL_TIMEOUT_MS / 1000) + " 秒）");
            throw new IOException("所有更新地址都无法访问 → " + String.join("；", errors));
        } finally {
            pool.shutdownNow();
        }
    }

    /** 把清单里的文件地址换成“当前可用镜像”的地址 */
    private String remoteFileUrl(Manifest m, JSONObject file, String fallbackName) {
        String name = file.optString("name", "");
        if (name.isEmpty()) {
            String u = file.optString("url", "");
            if (!u.isEmpty()) name = u.substring(u.lastIndexOf('/') + 1);
        }
        if (name.isEmpty()) name = fallbackName;
        if (m.filesBase != null && !m.filesBase.isEmpty()) return m.filesBase + name;
        return file.optString("url", "");
    }

    private static String hostOf(String url) {
        try {
            String h = new URL(url).getHost();
            return h == null ? url : h;
        } catch (Exception e) {
            return url;
        }
    }

    private static String describe(Throwable t) {
        if (t == null) return "未知错误";
        String msg = t.getMessage();
        String name = t.getClass().getSimpleName();
        if (msg == null || msg.trim().isEmpty()) return name;
        return name + ": " + msg;
    }

    // ---------------------------------------------------------------
    // 工具方法
    // ---------------------------------------------------------------
    private File getWebDir() {
        return new File(getContext().getFilesDir(), DIR_WEB);
    }

    private JSObject reply(String state, String msg, int webVersion, int appVersionCode,
                           String apkVersionName, boolean hasApk, String source) {
        JSObject ret = new JSObject();
        ret.put("state", state);
        ret.put("message", msg);
        ret.put("webVersion", webVersion);
        ret.put("appVersionCode", appVersionCode);
        ret.put("apkVersionName", apkVersionName);
        ret.put("hasApk", hasApk);
        ret.put("source", source == null ? "" : source);
        return ret;
    }

    /**
     * 当前生效的网页内容版本号。
     * 只有"热更新目录确实在被使用"时才读它，否则回落到安装包内置的基线版本，
     * 避免整包升级后误判（把新内容当成旧内容，或提示无用更新）。
     */
    private int getLocalWebVersion() {
        try {
            File webDir = getWebDir();
            String pref = getContext()
                    .getSharedPreferences("CapWebViewSettings", Context.MODE_PRIVATE)
                    .getString("serverBasePath", "");
            boolean usingHotUpdate = pref != null && !pref.isEmpty()
                    && new File(pref).getAbsolutePath().equals(webDir.getAbsolutePath());
            if (usingHotUpdate) {
                int v = readVersionFile(new File(webDir, "VERSION"));
                if (v > 0) return v;
            }
        } catch (Exception ignored) {}
        return readBundledVersion();
    }

    private int readVersionFile(File v) {
        try {
            if (v.isFile()) return Integer.parseInt(readFile(v).trim());
        } catch (Exception ignored) {}
        return 0;
    }

    /** 安装包 assets/public/VERSION 里记录的基线版本 */
    private int readBundledVersion() {
        try (InputStream in = getContext().getAssets().open("public/VERSION")) {
            StringBuilder sb = new StringBuilder();
            byte[] buf = new byte[256];
            int n;
            while ((n = in.read(buf)) != -1) sb.append(new String(buf, 0, n, StandardCharsets.UTF_8));
            return Integer.parseInt(sb.toString().trim());
        } catch (Exception e) {
            return 0;
        }
    }

    private void writeVersion(File webDir, int version) {
        try {
            writeFile(new File(webDir, "VERSION"), String.valueOf(version));
        } catch (Exception ignored) {}
    }

    private int currentVersionCode() {
        try {
            PackageManager pm = getContext().getPackageManager();
            if (Build.VERSION.SDK_INT >= 28) {
                return (int) pm.getPackageInfo(getContext().getPackageName(), 0).getLongVersionCode();
            }
            return pm.getPackageInfo(getContext().getPackageName(), 0).versionCode;
        } catch (PackageManager.NameNotFoundException e) {
            return 0;
        }
    }

    private String currentVersionName() {
        try {
            return getContext().getPackageManager().getPackageInfo(getContext().getPackageName(), 0).versionName;
        } catch (Exception e) {
            return "";
        }
    }

    private void persistTo(String path) {
        getContext().getSharedPreferences("CapWebViewSettings", Context.MODE_PRIVATE)
                .edit().putString("serverBasePath", path).apply();
    }

    private void promptInstall(File apkFile) {
        Uri apkUri = FileProvider.getUriForFile(getContext(),
                getContext().getPackageName() + ".fileprovider", apkFile);
        Intent intent = new Intent(Intent.ACTION_VIEW);
        intent.setDataAndType(apkUri, "application/vnd.android.package-archive");
        intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
        getActivity().startActivity(intent);
    }

    private File download(String urlStr, File target, int timeoutMs) throws IOException {
        File parent = target.getParentFile();
        if (parent != null && !parent.exists()) parent.mkdirs();
        HttpURLConnection conn = (HttpURLConnection) new URL(urlStr).openConnection();
        conn.setConnectTimeout(20000);
        conn.setReadTimeout(timeoutMs);
        conn.setRequestProperty("User-Agent", "Mozilla/5.0 (Linux; Android 12) AppleWebKit/537.36 Chrome/120 Mobile");
        conn.setInstanceFollowRedirects(true);
        int code = conn.getResponseCode();
        if (code == 301 || code == 302 || code == 303 || code == 307) {
            String loc = conn.getHeaderField("Location");
            conn.disconnect();
            if (loc == null) throw new IOException("重定向缺少 Location");
            return download(loc, target, timeoutMs);
        }
        if (code != 200) {
            conn.disconnect();
            throw new IOException("HTTP " + code);
        }
        try (InputStream in = new BufferedInputStream(conn.getInputStream());
             OutputStream out = new BufferedOutputStream(new FileOutputStream(target))) {
            byte[] buf = new byte[16384];
            int n;
            while ((n = in.read(buf)) != -1) out.write(buf, 0, n);
        } finally {
            conn.disconnect();
        }
        return target;
    }

    private JSONObject fetchJson(String urlStr, int timeoutMs) throws Exception {
        HttpURLConnection conn = (HttpURLConnection) new URL(urlStr).openConnection();
        conn.setConnectTimeout(15000);
        conn.setReadTimeout(timeoutMs);
        conn.setRequestProperty("User-Agent", "Mozilla/5.0 (Linux; Android 12) AppleWebKit/537.36 Chrome/120 Mobile");
        conn.setInstanceFollowRedirects(true);
        int code = conn.getResponseCode();
        if (code == 301 || code == 302 || code == 303 || code == 307) {
            String loc = conn.getHeaderField("Location");
            conn.disconnect();
            if (loc == null) throw new IOException("重定向缺少 Location");
            return fetchJson(loc, timeoutMs);
        }
        if (code != 200) {
            conn.disconnect();
            throw new IOException("HTTP " + code);
        }
        try (InputStream in = new BufferedInputStream(conn.getInputStream())) {
            StringBuilder sb = new StringBuilder();
            byte[] buf = new byte[8192];
            int n;
            while ((n = in.read(buf)) != -1) {
                sb.append(new String(buf, 0, n, StandardCharsets.UTF_8));
            }
            String body = sb.toString().trim();
            if (!body.startsWith("{")) {
                throw new IOException("返回内容不是 JSON（可能被网络拦截）");
            }
            return new JSONObject(body);
        } finally {
            conn.disconnect();
        }
    }

    private String readFile(File f) throws IOException {
        StringBuilder sb = new StringBuilder();
        try (InputStream in = new BufferedInputStream(new FileInputStream(f))) {
            byte[] buf = new byte[4096];
            int n;
            while ((n = in.read(buf)) != -1) sb.append(new String(buf, 0, n, StandardCharsets.UTF_8));
        }
        return sb.toString();
    }

    private void writeFile(File f, String content) throws IOException {
        try (OutputStream os = new BufferedOutputStream(new FileOutputStream(f))) {
            os.write(content.getBytes(StandardCharsets.UTF_8));
        }
    }

    private String sha256(File file) throws Exception {
        MessageDigest md = MessageDigest.getInstance("SHA-256");
        try (InputStream in = new BufferedInputStream(new FileInputStream(file))) {
            byte[] buf = new byte[16384];
            int n;
            while ((n = in.read(buf)) != -1) md.update(buf, 0, n);
        }
        StringBuilder hex = new StringBuilder();
        for (byte b : md.digest()) hex.append(String.format("%02x", b));
        return hex.toString();
    }

    private void unzip(File zip, File destDir) throws IOException {
        try (ZipFile zf = new ZipFile(zip)) {
            java.util.Enumeration<? extends ZipEntry> entries = zf.entries();
            while (entries.hasMoreElements()) {
                ZipEntry e = entries.nextElement();
                // 防止 ../ 穿越
                String entryName = e.getName().replace('\\', '/');
                if (entryName.startsWith("/") || entryName.contains("..")) continue;
                File out = new File(destDir, entryName);
                if (e.isDirectory()) {
                    if (!out.exists()) out.mkdirs();
                    continue;
                }
                File parent = out.getParentFile();
                if (parent != null && !parent.exists()) parent.mkdirs();
                try (InputStream in = new BufferedInputStream(zf.getInputStream(e));
                     OutputStream os = new BufferedOutputStream(new FileOutputStream(out))) {
                    byte[] buf = new byte[16384];
                    int n;
                    while ((n = in.read(buf)) != -1) os.write(buf, 0, n);
                }
            }
        }
    }

    private void deleteRecursive(File f) {
        if (f == null || !f.exists()) return;
        if (f.isDirectory()) {
            File[] children = f.listFiles();
            if (children != null) {
                for (File c : children) deleteRecursive(c);
            }
        }
        //noinspection ResultOfMethodCallIgnored
        f.delete();
    }
}