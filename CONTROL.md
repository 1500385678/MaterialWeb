# CONTROL.md · MaterialWeb v1.0 总控台

> **下一个 Agent 接手必读**。从零理解整个项目,看完这份 ≈ 5 分钟。
> 如果你只读一个文件,**读这个**。

---

## 0. 30 秒定位

**建筑材料数据库 + AI 选材工具** —— 看材料、创建项目、AI 识图选材、保存方案、导出 PDF。

| 维度 | 值 |
|---|---|
| 端口 | **8086**(CanvasWeb 8085 / v1 留对照) |
| 后端 | Flask + SQLite,**2 个 pip 依赖**(flask + qrcode + reportlab) |
| 前端 | 原生 ES Modules,**零 npm 依赖** |
| 数据 | SQLite + 文件系统(uploads / qr_codes / media) |
| 启动(Mac) | `python3 scripts/daemon.py`(后台) · `python3 -m server`(前台) |
| 启动(Win) | `python scripts\daemon.py`(后台) · `python -m server`(前台) |
| 验证 | `python3 tests/smoke.py` → `✅ 8/8 endpoints OK` |
| 体量 | **~3700 行** (Py 1850 + JS 1600 + HTML/CSS 450) |
| 工作目录 | `/Users/aaron/Mac/WorkTeam/05_Space/03_Architect/Defense/06-Material/_ArchiDefenseMaterial/MaterialWeb/` |

---

## 1. 全景架构(一张图)

```
┌──────────────────────────────────────────────────────────┐
│  Browser · http://127.0.0.1:8086                          │
│                                                            │
│  index.html  ← 入口 HTML(瘦,~250 行)                      │
│       ↓                                                    │
│  main.js  ← import + init()                                │
│       ↓                                                    │
│  ┌──────────────────────────────────────────┐              │
│  │  api.js       · 所有 /api/* 封装           │              │
│  │  core/        · state / dom / events / toast │              │
│  │  modules/     · 11 个业务模块               │              │
│  └──────────────────────────────────────────┘              │
└─────────────────────┬──────────────────────────────────────┘
                      │ HTTP
                      ↓
┌──────────────────────────────────────────────────────────┐
│  Python · python -m server  (port 8086)                  │
│                                                            │
│  __main__.py  · 入口                                        │
│  core.py      · Flask app + DB + CORS                      │
│  routes.py    · URL → handler 表                            │
│  handlers/    · 11 个业务端点                              │
└─────────────────────┬──────────────────────────────────────┘
                      ↓
┌──────────────────────────────────────────────────────────┐
│  Data Layer                                               │
│  ┌──────────────┐ ┌────────────┐ ┌──────────────────────┐ │
│  │ SQLite       │ │ 文件       │ │ 业务数据              │ │
│  │ materials.db │ │ uploads    │ │ 6 表(材料/项目/...)  │ │
│  │ (160KB)      │ │ qr_codes   │ │ 31 个 API 端点        │ │
│  │              │ │ media      │ │                      │ │
│  └──────────────┘ └────────────┘ └──────────────────────┘ │
└──────────────────────────────────────────────────────────┘
```

---

## 2. 一个请求的一生(从搜索材料到渲染卡片)

```
1. 用户在搜索框输入"花岗岩"
       ↓
2. filters.js 触发 searchMaterials()
       ↓
3. api.js 调 GET /api/materials?keyword=花岗岩
       ↓
4. server/__main__.py 接收
       ↓
5. routes.dispatch → handlers/materials.py:list_materials()
       ↓
6. SQLite 查询 → 返 JSON 列表
       ↓
7. materials.js 收到 list → 渲染卡片网格
       ↓
8. 用户点击卡片 → openDetail(id) → GET /api/materials/<id>
       ↓
9. handlers/materials.py:detail() → 返详情(含 suppliers)
       ↓
10. 弹窗打开,5 个 tab 切换基本信息/图片/CAD/构造/供应商
```

整个链路 < 50ms。SQLite 单文件锁,自动串行化。

---

## 3. 状态分布(关键心智模型)

| 状态 | 在哪 | 谁改 | 谁读 | 持久化? |
|---|---|---|---|---|
| 当前 tab | `utils.js` | 用户点击 | 全部 | ❌ |
| 材料列表 | `core/state.js` | materials.js | materials.js | ❌ 刷新丢 |
| 项目列表 | `core/state.js` | projects.js | projects.js | ❌ |
| 分类树 | `core/state.js` | filters.js | filters.js | ❌ |
| AI 流程状态 | `core/state.js` ai | ai-flow.js | ai-flow.js | ❌ |
| AI 模型配置 | localStorage | model-settings.js | model-settings.js | ✅ |
| 所有业务数据 | `db/materials.db` | 后端 handlers | 后端 handlers | ✅ 后端真源 |
| 用户上传图 | `data/uploads/` | ai-flow.js | api.js 返回 URL | ✅ |
| 二维码 | `data/qr_codes/` | qr handler | 浏览器直接访问 | ✅ |

> ⚠️ **关键**:浏览器刷新 = 前端 state 全丢,**SQLite 才是真源**。

---

## 4. 5 个必读文件(只看这 5 个就能改任何东西)

| 优先级 | 文件 | 行数 | 为什么 |
|---|---|---|---|
| 🔴 1 | [[MAIN]] | ~150 | 主程序/支程序边界,改之前三思 |
| 🔴 2 | `docs/AGENTS.md` | ~150 | AI 协作者硬约束清单 |
| 🔴 3 | `docs/api_contract.md` | ~200 | 所有 API 端点契约 |
| 🟡 4 | `client/js/core/state.js` | ~50 | 全局状态结构(其他都 import 它) |
| 🟡 5 | `server/routes.py` | ~25 | 后端所有 URL 的总入口 |

---

## 5. 关键铁律(违反就崩)

| # | 铁律 | 违反后果 |
|---|---|---|
| 1 | **单文件 ≤ 250 行** | 已超的标 v1.1 必拆 |
| 2 | **端口 8086** | 改 → 同步 config.py + daemon.py + 文档 |
| 3 | **API 路径只加不删** | 删字段会让 v0(5188)前端失效 |
| 4 | **API 响应字段只加不删** | 同上 |
| 5 | **HTML/CSS/JS 全部 no-store**(白名单: text/html, text/css, application/javascript, text/javascript · 精确 MIME,小写,不含 charset) | 否则 AI 改完不生效 |
| 6 | **写权限限本机 IP** | dev 默认 127.0.0.1 + 写前 IP 白名单中间件;LAN 例外靠 `MW_HOST=0.0.0.0 MW_ALLOWED_LAN_IPS=<...>` 临时开 |
| 7 | **并发上限 20** | 超出 503 |
| 8 | **用 bus 跨模块,别直接 import 内部变量** | 循环依赖 |

完整铁律见 `docs/AGENTS.md` § 3。

---

## 6. 当前状态(2026-07-13)

### ✅ 工作正常
- 服务在跑,8086 在听
- 8/8 端点 smoke test 通过
- 主流程:看材料 → 创建项目 → AI 选材 → 保存方案 → 导出 PDF
- 数据已迁移:materials.db 160KB + 11 张 AI 图 + 4 个 QR
- 已关闭 werkzeug watchdog reloader(2026-08-10 夜间迭代修):daemon 启动强制 `MW_DEBUG=0`,server.out 不再每改文件整进程重启,启动 banner 打印 `MW_DEBUG=0, reloader=off` 便于排错
- search_by_analysis 加 SQL 预过滤(2026-08-11 夜间迭代批 2 改 · P1):_PRE_FILTER_LIMIT=500 + 抽 _score_row + 8 字段精排;1000 行 fixture P95 < 200ms 契约(tests/search_bench.py)
- Cache-Control 改白名单精确匹配(2026-08-11 夜间迭代批 2 改 · P2):substring('javascript') → set 查 {text/html, text/css, application/javascript, text/javascript},加 Vary: Accept-Encoding 防 gzip 缓存串(tests/test_cache_headers.py 覆盖 .html/.css/.js/.png/JSON 五场景)

### ⚠️ 已知问题
- Flask 保留(偏离 v2.5 § 6.2 铁律,因 PDF/二维码需要)
- docx 导出暂用 JSON placeholder(v1.0 后续接 docx 库)
- 旧 `MaterialDb/` 目录还在原位(WPS 锁,未删除),可手动清
- LAN 暴露(2026-08-08 已修 P0①):daemon 历史绑 0.0.0.0 + CORS=*,违反铁律 #6;已改默认 127.0.0.1 + 写前 IP 白名单中间件,LAN 临时开放需 `MW_HOST=0.0.0.0 MW_ALLOWED_LAN_IPS=<ip>` 显式声明

### ❌ 工程化债(详见 .Log)
| 优先级 | 项 | 估时 |
|---|---|---|
| 🔴 P0-① | 拆 0 个文件(暂时都 ≤250 行) | 0h |
| 🟡 P1-② | docx 真实导出(目前 JSON 占位) | 1h |
| 🟡 P1-③ | 清理旧 MaterialDb/ | 5min |
| ⚪ P2-④ | 7 份 docs 完整版 | 2h |
| ⚪ P2-⑤ | 移动数据目录到 %LOCALAPPDATA% | 0.5d |

---

## 7. 接手 5 步(给下一个 Agent)

```
1. 读 [[CONTROL]]                    ← 本文件,5 分钟
2. 读 [[MAIN]]                        ← 主程序/支程序边界,3 分钟
3. 读 docs/AGENTS.md                  ← 硬约束 + 加新功能流程,10 分钟
4. python scripts/daemon.py           ← 启动,1 分钟
5. python tests/smoke.py              ← 验证 8 端点,1 分钟
                                      ─────────────
                                       合计 20 分钟
```

之后挑一个 P1 干。干完一个在 [[.Log/]] 加一条日志。

---

## 8. 关键链接

### 必读(上手)
- [[README]] · 小白入门版
- [[MAIN]] · 主程序/支程序边界
- `docs/AGENTS.md` · AI 协作者硬约束
- `docs/api_contract.md` · API 契约(所有端点)
- `docs/FILE_GUIDE.md` · 3-5 行/文件详释
- `docs/CHEATSHEET.md` · 1 行/文件速查

### 速查
- `docs/STYLE.md` · 代码风格
- `docs/WORKFLOWS.md` · 8 阶段工作流

### 兄弟模块(在 _ArchitectLib/ 根)
- `CanvasWeb-v2.5/` · 画布工具(端口 8085)
- `PictureDb/PictureDb.db` · 共享图库(只读)
- `_archive_2026-07-13_MaterialWeb/` · 旧 monolith 备份

---

## 9. 应急联系(出问题时)

| 现象 | 先看 |
|---|---|
| 启动失败 | `daemon.out` / `daemon.err`(本目录) |
| 端点 500 | `server.out` / `server.err`(本目录) |
| 前端不刷新 | 浏览器硬刷 Ctrl+Shift+R(已 no-store) |
| 数据丢失 | 检查 `data/uploads/` `data/qr_codes/` 还在不在 |
| 端口冲突 (Mac) | `lsof -ti:8086 \| xargs kill -9`(杀 8086 进程) |
| 端口冲突 (Win) | `netstat -ano -p TCP \| findstr :8086` 杀 PID |

---

> 变更记录
> - 2026-07-13 · 初版 · 由 03_Architect 创建,给下一个 agent 接手用
