# MaterialWeb · 自动发布流程

> 改完代码 → 一行命令 → commit + push + GitHub Release

---

## 0. 前置(已完成一次)

```powershell
# 1. GitHub PAT 写到 User-scope(本机所有进程可读,不入 git)
[Environment]::SetEnvironmentVariable('GH_TOKEN', 'ghp_xxx', 'User')

# 2. 验证
gh auth status   # 应该看到 "Logged in ... (GH_TOKEN)"
```

---

## 1. 日常用法

### 默认(自增修订号 v0.0.X)

```powershell
# PowerShell
powershell -File scripts\_commit_push.ps1 "feat: 加了 X"

# 或 CMD
scripts\_commit_push.bat "feat: 加了 X"

# 或双击 scripts\_commit_push.bat(消息用默认 "auto: update")
```

### 显式 bump

```powershell
# 修订号 v0.0.1 → v0.0.2
powershell -File scripts\_commit_push.ps1 "fix: 修了 Y" patch

# 次版本 v0.1.0
powershell -File scripts\_commit_push.ps1 "feat: 加新模块" minor

# 主版本 v1.0.0
powershell -File scripts\_commit_push.ps1 "breaking: 重构" major
```

### 流程

1. `git add -A` 全部 stage
2. `git commit -m "<消息>"`
3. `git push origin main` (HTTP/1.1 强制)
4. 调 `_release.ps1`:
   - 读 GitHub 最新 release tag
   - 自增版本号
   - 生成 notes(上次 release 后的 commits)
   - `gh release create vX.Y.Z --notes ...`

---

## 2. 团队同步机制

每次 release 创建后,**自动通知以下 agent**:

| Agent | 工作区 | 必读动作 |
|---|---|---|
| **Architect** | `05_Space/03_Architect` | `git pull` MaterialWeb + 看 release notes |
| **Engineer** | `05_Space/04_Engineer` | 同上,关注 API/字段变更 |
| **Manager-loc** | `05_Space/05_Manager` | 同步状态,任务看板更新 |
| **01_Owner** | `05_Space/01_Owner` | 决策是否升级到项目里用 |

**通知方式**:
1. **GitHub Releases** (`https://github.com/1500385678/MaterialWeb/releases`) — 权威源
2. **`docs/RELEASE.md`** (本文件) — 流程说明
3. **每次 release 的 notes 顶部写明同步对象** — `_release.ps1` 已自动加
4. **Mavis session 通知** — 调 `mavis` 工具给相关 agent root session 发消息(本流程**未默认开启**,如要开启见 § 3)

---

## 3. 想开启 Mavis session 自动广播

```powershell
# 给 Architect / Engineer / Manager-loc / 01_Owner 各发一条 release 通知
# (需在他们的 active session 上做)
mavis session messages --agent Architect --limit 1
# 然后用 mavis 工具的 session write 注入消息
```

(具体 mavis session 注入 API 待补,目前走 git log + release notes 通知)

---

## 4. 不要做的事

- **不要手动改版本号文件** — `_release.ps1` 自动管
- **不要 force-push / amend 已推 commit** — 会让 release notes 错位
- **不要直接改 `docs/RELEASE.md` 的流程说明** — 改了 `git pull` 同步不到(?)
  (开玩笑的,这是文档,改就改;但流程逻辑在 `_release.ps1` 里,以那个为准)

---

## 5. 故障排查

| 现象 | 原因 | 修法 |
|---|---|---|
| `GH_TOKEN not set` | User-scope 变量没设 | 重设并**新开 PowerShell** |
| `not a git repo` | 当前目录没 `.git` | `cd` 到项目根 |
| `origin not a GitHub repo` | remote URL 配错 | `git remote set-url origin https://github.com/1500385678/MaterialWeb.git` |
| `403 / Permission denied` | token 过期或 scopes 缺 `repo` | 重新生成 PAT(勾 `repo` + `workflow`) |
| `gh release create` 报"already exists" | tag 已存在 | 手动删 `gh release delete vX.Y.Z` 再重跑 |
