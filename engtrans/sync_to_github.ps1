# ============================================================
#  一键：把 engtrans 源码同步到 GitHub 仓库并推送
#  由 推送到GitHub.bat 调用（bat 只负责用 PowerShell 启动本脚本）
#  安全：自动排除 tools\ (1.9G)、node_modules、build、*.keystore
# ============================================================

$ErrorActionPreference = 'Continue'

$src  = $PSScriptRoot
$repo = 'D:\Deepseekworkplace\yzc-repo'

function Pause-End($code) {
    Write-Host ''
    try { Read-Host '按回车键关闭窗口' | Out-Null } catch { }
    exit $code
}

if (-not (Test-Path (Join-Path $repo '.git'))) {
    Write-Host "[错误] 找不到仓库目录：$repo" -ForegroundColor Red
    Write-Host '请先执行：'
    Write-Host '    cd /d D:\Deepseekworkplace'
    Write-Host '    git clone https://github.com/yzc-good/-.git yzc-repo'
    Pause-End 1
}

Write-Host '============================================================'
Write-Host "  源目录：$src"
Write-Host "  仓库  ：$repo"
Write-Host '============================================================'
Write-Host ''

# ---------- 1) 复制源码 ----------
Write-Host '[1/4] 复制源码（排除大目录与密钥）...'
$null = & robocopy $src (Join-Path $repo 'engtrans') /E `
    /XD tools node_modules build .gradle __pycache__ assets .idea .git `
    /XF *.apk *.keystore *.jks *.idsig local.properties `
    /NFL /NDL /NJH /NJS /NP
if ($LASTEXITCODE -ge 8) {
    Write-Host '[错误] 复制失败（robocopy 返回 '$LASTEXITCODE'）' -ForegroundColor Red
    Pause-End 1
}

# ---------- 2) 安全检查 ----------
Write-Host '[2/4] 安全检查...'
foreach ($bad in @('tools', 'node_modules', 'engtrans.keystore')) {
    if (Test-Path (Join-Path $repo "engtrans\$bad")) {
        Write-Host "[中止] 发现不该存在的项：$bad" -ForegroundColor Red
        Pause-End 1
    }
}

# ---------- 3) 暂存与提交 ----------
Write-Host '[3/4] 暂存改动...'
& git -C $repo add -A
if ($LASTEXITCODE -ne 0) {
    Write-Host '[错误] git add 失败' -ForegroundColor Red
    Pause-End 1
}

& git -C $repo diff --cached --quiet
$hasChanges = ($LASTEXITCODE -ne 0)

if ($hasChanges) {
    $msg = Read-Host '请输入本次改动说明（直接回车用默认）'
    if ([string]::IsNullOrWhiteSpace($msg)) { $msg = '更新英语翻译助手' }

    # 用 .NET 直接写 UTF-8（无 BOM），避免中文提交信息乱码
    $msgFile = Join-Path $repo '.git\ENGTRANS_COMMIT_MSG.txt'
    [IO.File]::WriteAllText($msgFile, $msg, (New-Object System.Text.UTF8Encoding($false)))
    & git -C $repo commit -F $msgFile
    Remove-Item $msgFile -Force -ErrorAction SilentlyContinue
    if ($LASTEXITCODE -ne 0) {
        Write-Host '[错误] 提交失败' -ForegroundColor Red
        Pause-End 1
    }
} else {
    Write-Host '      没有新改动，跳过提交'
}

# ---------- 4) 推送（github.com 在国内时通时不通，自动重试） ----------
Write-Host '[4/4] 推送到 GitHub...'

$maxTry = 6
$pushed = $false
$lastOut = ''

for ($i = 1; $i -le $maxTry; $i++) {
    $out = & git -C $repo push 2>&1
    $code = $LASTEXITCODE
    # 用 -join 保留原始行；不能用 Out-String，它会按窗口宽度折行，
    # 把 SEC_E_NO_CREDENTIALS 这类关键字拆断，导致后面识别失败
    $lastOut = (($out | ForEach-Object { "$_" }) -join "`n")
    $flat = $lastOut -replace "`r?`n", ' '

    if ($code -eq 0) {
        $out | ForEach-Object { Write-Host "      $_" }
        $pushed = $true
        break
    }

    # 认证类错误重试没意义，直接报
    if ($flat -match 'SEC_E_NO_CREDENTIALS|Authentication failed|Permission denied|403') {
        $out | ForEach-Object { Write-Host "      $_" -ForegroundColor DarkGray }
        break
    }

    if ($i -lt $maxTry) {
        Write-Host ("      第 $i 次连接失败（github.com 不稳定），5 秒后重试 $i/$maxTry ...") -ForegroundColor Yellow
        Start-Sleep -Seconds 5
    }
}

if (-not $pushed) {
    $flat = $lastOut -replace "`r?`n", ' '
    Write-Host ''
    if ($flat -match 'SEC_E_NO_CREDENTIALS') {
        Write-Host '[推送失败] 凭据问题（不是网络问题）。先执行这条再重试：' -ForegroundColor Yellow
        Write-Host '       git config --global http.sslBackend openssl'
    }
    elseif ($flat -match 'Authentication failed|Permission denied|403') {
        Write-Host '[推送失败] 认证失败。' -ForegroundColor Yellow
        Write-Host '  密码处要填 Personal Access Token（不是账号密码）：'
        Write-Host '    GitHub → Settings → Developer settings → Personal access tokens'
        Write-Host '    → Tokens (classic) → Generate new token → 勾选 repo → 复制'
    }
    elseif ($flat -match 'Failed to connect|Could not connect|port 443|timed out|Connection refused') {
        Write-Host '[推送失败] 连不上 github.com:443 —— 网络对 GitHub 的连接不稳定，不是你操作错了。' -ForegroundColor Yellow
        Write-Host '  已自动重试 6 次仍失败，可以这样做：'
        Write-Host '    a) 再双击一次本脚本（换个时机常常就通了）'
        Write-Host '    b) 换网络：用手机热点，或开代理/VPN 后再试'
        Write-Host '    c) 用浏览器打开仓库 update/ 目录，把这几个文件拖进去上传：'
        Write-Host '         publish_update\update.json'
        Write-Host '         publish_update\web-*.zip'
    }
    else {
        Write-Host '[推送失败] 原始输出：' -ForegroundColor Yellow
        Write-Host $lastOut
    }
    Pause-End 1
}

Write-Host ''
Write-Host '============================================================'
Write-Host '  完成！仓库地址：https://github.com/yzc-good/-'
Write-Host '============================================================'
Pause-End 0
