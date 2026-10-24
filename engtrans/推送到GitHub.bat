@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

rem ============================================================
rem  一键：把本目录的源码同步到 GitHub 仓库并推送
rem  用法：双击运行，按提示输入本次改动说明
rem  安全：自动排除 tools\ (1.9G)、node_modules、build、*.keystore
rem ============================================================

set "SRC=%~dp0"
if "%SRC:~-1%"=="\" set "SRC=%SRC:~0,-1%"
set "REPO=D:\Deepseekworkplace\yzc-repo"

if not exist "%REPO%\.git" (
    echo [错误] 找不到仓库目录：%REPO%
    echo 请先执行：
    echo     cd /d D:\Deepseekworkplace
    echo     git -c http.sslBackend=openssl clone https://github.com/yzc-good/-.git yzc-repo
    pause
    exit /b 1
)

echo ============================================================
echo  源目录：%SRC%
echo  仓库  ：%REPO%
echo ============================================================
echo.

echo [1/4] 复制源码（排除大目录与密钥）...
robocopy "%SRC%" "%REPO%\engtrans" /E /XD tools node_modules build .gradle __pycache__ assets .idea .git /XF *.apk *.keystore *.jks *.idsig local.properties /NFL /NDL /NJH /NJS /NP >nul
if errorlevel 8 goto :err_copy

echo [2/4] 安全检查...
if exist "%REPO%\engtrans\tools" goto :err_leak
if exist "%REPO%\engtrans\node_modules" goto :err_leak

echo [3/4] 暂存改动...
git -C "%REPO%" add -A
if errorlevel 1 goto :err_add

git -C "%REPO%" diff --cached --quiet
if errorlevel 1 goto :do_commit
echo       没有新改动，跳过提交
goto :do_push

:do_commit
set "MSG="
set /p "MSG=请输入本次改动说明（直接回车用默认）："
if "!MSG!"=="" set "MSG=更新英语翻译助手"
git -C "%REPO%" commit -m "!MSG!"
if errorlevel 1 goto :err_commit

:do_push
echo [4/4] 推送到 GitHub...
git -C "%REPO%" push
if errorlevel 1 goto :err_push

echo.
echo ============================================================
echo   完成！仓库地址：https://github.com/yzc-good/-
echo ============================================================
pause
exit /b 0

:err_copy
echo [错误] 复制失败（robocopy）
pause
exit /b 1

:err_leak
echo [中止] 发现不该存在的目录（tools 或 node_modules），已停止推送
pause
exit /b 1

:err_add
echo [错误] git add 失败
pause
exit /b 1

:err_commit
echo [错误] 提交失败
pause
exit /b 1

:err_push
echo.
echo [推送失败] 常见原因：
echo   1) 需要登录：首次推送会弹出浏览器授权窗口，按提示登录 GitHub
echo   2) 若报 SEC_E_NO_CREDENTIALS，先执行：
echo        git config --global http.sslBackend openssl
echo   3) 若提示密码错误：密码处要填 Personal Access Token，不是账号密码
pause
exit /b 1
