# 2026-07-23 · MaterialWeb 自动发布上线

## 干完了什么

MaterialWeb 接入**自动 commit + push + GitHub Release** 流程,改完代码一行命令出 release。

## 三个新文件

| 文件 | 作用 |
|---|---|
| `scripts/_commit_push.ps1` | 一键 `git add + commit + push`,可选 bump 类型 |
| `scripts/_commit_push.bat` | Windows 双击版,带 UTF-8 chcp |
| `scripts/_release.ps1` | 自动 bump 版本号 (vX.Y.Z→vX.Y.(Z+1)) + 创建 GitHub Release |
| `docs/RELEASE.md` | 流程文档 + 团队同步机制 + 故障排查 |
| `.gitattributes` | 统一行尾 LF,避免 Windows CRLF 污染 diff |

## 已发布的 release

- **v0.0.1** — UI 改版 (sidebar+hero+entry+大图网格) + 端口 8092 + 自动 release 脚本
- **v0.0.2** — `_release.ps1` 反引号转义修复 + `.gitattributes` 统一 LF

GitHub: https://github.com/1500385678/MaterialWeb/releases

## 用法(以后)

```powershell
# 日常:改完代码后
powershell -File scripts\_commit_push.ps1 "feat: 加了 X"

# 显式 bump
powershell -File scripts\_commit_push.ps1 "fix: 修了 Y" minor   # v0.0.2 → v0.1.0
powershell -File scripts\_commit_push.ps1 "breaking" major       # v0.0.2 → v1.0.0
```

## "告诉所有 agent" 的实现机制

mavis runtime **不支持**主动 session-to-session 发消息(参考 `references/session-and-communication.md`)。

替代机制(全部已启用):
1. **GitHub Releases** (权威源) - `https://github.com/1500385678/MaterialWeb/releases`
2. **Release notes 顶部明确列出同步对象** - `Architect / Engineer / Manager-loc / 01_Owner`
3. **commit message** 标 `fix:` / `feat:` / `breaking:` 前缀
4. **`docs/RELEASE.md`** 流程文档 - 团队 git pull 后看到
5. **用户用飞书/IM 广播** - MaterialWeb 自动发布上线消息

## 已知坑

- **网络瞬断**:push 偶尔 60s 超时,retry 1-2 次 + 切 HTTP/1.1 强制 (`$env:GIT_HTTP_VERSION='HTTP/1.1'`) 通常能过
- **autocrlf=true** 在 Windows 下导致 staged diff 看着像 M,实际只是 line ending 差异
- **PowerShell here-string (`@" "@`)** 在 PS 5.1 解析要求文件是 CRLF,LF-only 会报 "missing terminator"
  - 解决:文件先 CRLF 化(用 .NET WriteAllText)
  - 解决:不写 PS1,改用 .py 写文件
- **Manager-loc agent 不在 mavis list 里** - 可能用别的名字或没建

## 同步对象

- Architect (`agent-8be311ed26e2`)
- 04_Engineer (`agent-bb77adedc420`)
- 01_Owner (`agent-4e0bf93f6e41`)
- Manager-loc (mavis list 没找到,待确认)
