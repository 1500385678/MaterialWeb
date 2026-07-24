# _release.ps1 · 自动 bump 版本号 + 创建 GitHub Release
# 策略: 自增修订号 (vX.Y.Z → vX.Y.(Z+1))
# 依赖: gh CLI 已配置 GH_TOKEN (User-scope 即可)
# 用法: powershell -File scripts\_release.ps1          # 自增 .Z
#       powershell -File scripts\_release.ps1 major     # +1 主版本
#       powershell -File scripts\_release.ps1 minor     # +1 次版本

param(
    [ValidateSet('patch', 'minor', 'major')]
    [string]$Bump = 'patch'
)

$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $PSScriptRoot)

# 1. 取 token + 注入 process (gh 识别 GH_TOKEN 环境变量)
$token = [Environment]::GetEnvironmentVariable('GH_TOKEN', 'User')
if (-not $token) { Write-Error "[release] GH_TOKEN not set in User-scope. Run: [Environment]::SetEnvironmentVariable('GH_TOKEN','ghp_xxx','User')"; exit 1 }
$env:GH_TOKEN = $token

# 2. 拿仓库 origin 推导 owner/repo
$remote = git remote get-url origin
if ($remote -notmatch 'github\.com[:/](.+?)/(.+?)\.git$') { Write-Error "[release] origin not a GitHub repo: $remote"; exit 1 }
$owner = $matches[1]; $repo = $matches[2]

# 3. 读最新 release tag (从 GitHub API 拿,不走 git fetch)
$latest = gh release list --repo "$owner/$repo" --limit 1 --json tagName -q '.[0].tagName' 2>$null
if (-not $latest) { $next = 'v0.0.1'; $prev = $null }
else {
    if ($latest -match '^v(\d+)\.(\d+)\.(\d+)$') {
        $maj = [int]$matches[1]; $min = [int]$matches[2]; $pat = [int]$matches[3]
        switch ($Bump) {
            'major' { $maj += 1; $min = 0; $pat = 0 }
            'minor' { $min += 1; $pat = 0 }
            default  { $pat += 1 }
        }
        $next = "v$maj.$min.$pat"
    } else {
        Write-Warning "[release] latest tag '$latest' 不符合 vX.Y.Z, 回退 v0.0.1"
        $next = 'v0.0.1'
    }
    $prev = $latest
}

# 4. 收集 release notes (上次 release 之后的 commit,从 GitHub API 拿,避免本地 tag 缺失)
$logLines = @()
$base = if ($prev) { $prev } else { $null }
if ($base) {
    try {
        $compareOut = gh api "repos/$owner/$repo/compare/$base...main" --jq '.commits[].commit.message' 2>$null
        if ($compareOut) {
            foreach ($line in ($compareOut -split "`n")) {
                $first = ($line -split "`n")[0].Trim()
                if ($first.Length -gt 0) { $logLines += "- $first" }
            }
        }
    } catch {}
}
# fallback: 用本地 git log (可能因 tag 缺失而只返 HEAD)
if (-not $logLines) {
    try {
        $headSha = git rev-parse HEAD
        $localLog = git log --pretty=format:"- %s" -n 5 $headSha 2>$null
        if ($localLog) { $logLines = @($localLog) }
    } catch {}
}
if (-not $logLines) { $logLines = @("- 初始 release $next") }
$log = $logLines -join "`n"
$today = Get-Date -Format 'yyyy-MM-dd HH:mm'
$notes = @"
## MaterialWeb $next

发布日期: $today
触发: 自动 release (scripts\_release.ps1 -$Bump)

### 变更
$log

### 同步
- Architect / Engineer / Manager-loc / 01_Owner 请同步本地代码 + 查看 release notes
- 安装: `git pull origin main`
"@

# 5. 创建 release (用临时文件传 notes 避免转义问题)
$notesFile = Join-Path $env:TEMP "release-notes-$next.md"
$notes | Out-File -FilePath $notesFile -Encoding UTF8

Write-Host "[release] latest=$latest  next=$next  bump=$Bump"
gh release create $next `
    --repo "$owner/$repo" `
    --title "MaterialWeb $next" `
    --notes-file $notesFile `
    --target main

Remove-Item $notesFile -Force -ErrorAction SilentlyContinue
Write-Host "[release] OK · https://github.com/$owner/$repo/releases/tag/$next"
