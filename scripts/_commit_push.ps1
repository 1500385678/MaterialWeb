# _commit_push.ps1 · 一键 commit + push + release
# 用法:
#   powershell -File scripts\_commit_push.ps1                      # 默认消息 "auto: update"
#   powershell -File scripts\_commit_push.ps1 "feat: 加了 X"        # 自定义消息
#   powershell -File scripts\_commit_push.ps1 "fix: 修了 Y" minor   # bump 次版本
#   powershell -File scripts\_commit_push.ps1 "breaking" major      # bump 主版本
# 依赖: GH_TOKEN 已在 User-scope
# 后置: 自动调 _release.ps1 (默认 patch,传 minor/major 切换)

param(
    [Parameter(Position=0)][string]$Message = 'auto: update',
    [Parameter(Position=1)][ValidateSet('patch','minor','major')][string]$Bump = 'patch'
)

$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $PSScriptRoot)

# 1. 装 token 到 process
$token = [Environment]::GetEnvironmentVariable('GH_TOKEN', 'User')
if (-not $token) { Write-Error "[commit_push] GH_TOKEN not set in User-scope"; exit 1 }
$env:GH_TOKEN = $token

# 2. 检查 repo
if (-not (Test-Path .git)) { Write-Error "[commit_push] not a git repo (cwd=$PWD)"; exit 1 }

# 3. stage + 看是否有改动
git add -A
$porcelain = git status --porcelain
if (-not $porcelain) {
    Write-Host "[commit_push] 无改动,跳过 commit/push/release"
    exit 0
}
Write-Host "[commit_push] 待提交:"
$porcelain | ForEach-Object { Write-Host "  $_" }

# 4. commit
$ts = Get-Date -Format 'yyyy-MM-dd HH:mm'
git commit -m "$Message" -m "auto: $ts"

# 5. push (HTTP/1.1 强兼容,GitHub Windows 偶尔 HTTP/2 卡死)
$env:GIT_HTTP_VERSION = 'HTTP/1.1'
git push origin main

# 6. release
& "$PSScriptRoot\_release.ps1" -Bump $Bump
