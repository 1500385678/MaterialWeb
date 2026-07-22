# MaterialWeb v1.0 · Windows 一键启动
# 端口 8086 · 后台跑(关窗口不退出)
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $PSScriptRoot)
python scripts/daemon.py
