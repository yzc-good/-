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

# ---------- 4) 推送 ----------
Write-Host '[4/4] 推送到 GitHub...'
& git -C $repo push
if ($LASTEXITCODE -ne 0) {
    Write-Host ''
    Write-Host '[推送失败] 常见原因：' -ForegroundColor Yellow
    Write-Host '  1) 需要登录：首次推送会弹出浏览器授权窗口，按提示登录 GitHub'
    Write-Host '  2) 若报 SEC_E_NO_CREDENTIALS，先执行：'
    Write-Host '       git config --global http.sslBackend openssl'
    Write-Host '  3) 若提示密码错误：密码处要填 Personal Access Token，不是账号密码'
    Pause-End 1
}

Write-Host ''
Write-Host '============================================================'
Write-Host '  完成！仓库地址：https://github.com/yzc-good/-'
Write-Host '============================================================'
Pause-End 0
