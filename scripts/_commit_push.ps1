# _commit_push.ps1 · 一键 commit + push(双平台) + release
# 用法:
#   powershell -File scripts\_commit_push.ps1                      # 默认消息 "auto: update"
#   powershell -File scripts\_commit_push.ps1 "feat: 加了 X"        # 自定义消息
#   powershell -File scripts\_commit_push.ps1 "fix: 修了 Y" minor   # bump 次版本
#   powershell -File scripts\_commit_push.ps1 "breaking" major      # bump 主版本
# 依赖: GH_TOKEN 已在 User-scope
# 后置: 自动调 _release.ps1 (默认 patch,传 minor/major 切换)
# 双平台:GitHub(origin) + Gitee(remote gitee)
#   Gitee PAT 读 GITEE_TOKEN(优先)或从 GH_TOKEN 退化(都不行就 warn 跳过)

param(
    [Parameter(Position=0)][string]$Message = 'auto: update',
    [Parameter(Position=1)][ValidateSet('patch','minor','major')][string]$Bump = 'patch'
)

$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $PSScriptRoot)

# 1. 装 token 到 process
$ghToken = [Environment]::GetEnvironmentVariable('GH_TOKEN', 'User')
$giteeToken = [Environment]::GetEnvironmentVariable('GITEE_TOKEN', 'User')
if (-not $ghToken) { Write-Error "[commit_push] GH_TOKEN not set in User-scope"; exit 1 }
$env:GH_TOKEN = $ghToken

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

# 5a. GitHub
$ghOk = $true
try { git push origin main 2>&1 | Out-Null } catch { $ghOk = $false; Write-Warning "[commit_push] GitHub push failed: $_" }
if ($ghOk) { Write-Host "[commit_push] GitHub push OK" }

# 5b. Gitee (双平台同步,互不依赖)
if ($giteeToken) {
    $giteeRemote = "gitee"
    $hasGitee = (git remote | Select-String -Pattern '^gitee$') -ne $null
    if (-not $hasGitee) {
        Write-Host "[commit_push] 配 gitee remote https://oauth2:***@gitee.com/architectzy/MaterialWeb.git"
        git remote add gitee "https://oauth2:$giteeToken@gitee.com/architectzy/MaterialWeb.git"
    } else {
        # 已有 remote 但 token 可能过期,更新 URL
        $curUrl = git remote get-url $giteeRemote
        if ($curUrl -notlike "*oauth2*") {
            git remote set-url $giteeRemote "https://oauth2:$giteeToken@gitee.com/architectzy/MaterialWeb.git"
        }
    }
    try {
        git fetch $giteeRemote --tags 2>&1 | Out-Null
        git push $giteeRemote main --tags 2>&1 | Out-Null
        Write-Host "[commit_push] Gitee push OK"
    } catch {
        Write-Warning "[commit_push] Gitee push failed: $_"
    }
} else {
    Write-Host "[commit_push] GITEE_TOKEN 未设,跳过 Gitee push(设了之后双平台同步)"
}

# 6. release (只发 GitHub,本版本)
& "$PSScriptRoot\_release.ps1" -Bump $Bump
