@echo off
REM _commit_push.bat · Windows 双击版
REM 默认 patch bump;想 minor / major 把最后一行 _release.ps1 -Bump patch 改掉
chcp 65001 >nul
cd /d "%~dp0\.."
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0\_commit_push.ps1" %*
